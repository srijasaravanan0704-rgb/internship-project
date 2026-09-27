"""
Cryptocurrency Price Tracker — Scraper
---------------------------------------
Scrapes the top 15 cryptocurrencies from CoinMarketCap using Selenium,
and writes the results to data/latest.json (for the dashboard) and
data/history.csv (timestamped log for trend analysis).

Usage:
    python scraper.py                 # scrape once, visible browser
    python scraper.py --headless      # scrape once, no browser window
    python scraper.py --loop 300      # scrape every 300 seconds, forever
    python scraper.py --top 15 --min-change -100 --max-change 100
"""

import argparse
import csv
import json
import os
import time
from datetime import datetime, timezone

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
LATEST_JSON = os.path.join(DATA_DIR, "latest.json")
HISTORY_CSV = os.path.join(DATA_DIR, "history.csv")
URL = "https://coinmarketcap.com/"

CSV_FIELDS = [
    "timestamp", "rank", "name", "symbol", "price",
    "change_1h", "change_24h", "change_7d", "market_cap", "volume_24h",
]


def build_driver(headless: bool) -> webdriver.Chrome:
    """Configure and return a Chrome WebDriver instance."""
    options = Options()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--window-size=1600,1000")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    )
    # Reduces obvious "controlled by automation software" fingerprints.
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.execute_cdp_cmd(
        "Page.addScriptToEvaluateOnNewDocument",
        {"source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"},
    )
    return driver


def _clean_number(text: str):
    """Turn '$56,190.30', '1.4%', '$1.10T' style strings into floats where possible."""
    if text is None:
        return None
    t = text.strip().replace(",", "").replace("$", "").replace("%", "")
    multiplier = 1
    if t.endswith("T"):
        multiplier, t = 1_000_000_000_000, t[:-1]
    elif t.endswith("B"):
        multiplier, t = 1_000_000_000, t[:-1]
    elif t.endswith("M"):
        multiplier, t = 1_000_000, t[:-1]
    elif t.endswith("K"):
        multiplier, t = 1_000, t[:-1]
    try:
        return round(float(t) * multiplier, 6)
    except ValueError:
        return None


def scrape_top_coins(driver: webdriver.Chrome, top_n: int = 15) -> list[dict]:
    """Scrape the top_n coins from CoinMarketCap's main table."""
    driver.get(URL)
    wait = WebDriverWait(driver, 20)
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table")))
    # The table lazy-renders rows as you scroll; nudge it a couple of times.
    for _ in range(3):
        driver.execute_script("window.scrollBy(0, 900);")
        time.sleep(1)

    rows = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")[:top_n]
    coins = []
    for i, row in enumerate(rows, start=1):
        try:
            cells = row.find_elements(By.TAG_NAME, "td")
            name_block = row.find_element(By.CSS_SELECTOR, "p, span")
            full_name_text = row.text.split("\n")
            name = full_name_text[2] if len(full_name_text) > 2 else name_block.text
            symbol = full_name_text[3] if len(full_name_text) > 3 else ""

            price_el = row.find_element(By.CSS_SELECTOR, "[data-testid='price'], td:nth-child(4)")
            coins.append({
                "rank": i,
                "name": name.strip(),
                "symbol": symbol.strip().upper(),
                "price": _clean_number(price_el.text),
                "change_1h": _clean_number(cells[4].text) if len(cells) > 4 else None,
                "change_24h": _clean_number(cells[5].text) if len(cells) > 5 else None,
                "change_7d": _clean_number(cells[6].text) if len(cells) > 6 else None,
                "market_cap": _clean_number(cells[7].text) if len(cells) > 7 else None,
                "volume_24h": _clean_number(cells[8].text) if len(cells) > 8 else None,
            })
        except Exception as exc:  # noqa: BLE001 — keep scraping remaining rows
            print(f"  ! skipped row {i}: {exc}")
            continue
    return coins


def filter_coins(coins: list[dict], min_change=None, max_change=None) -> list[dict]:
    """Optional filtering by 24h change threshold (Feature: custom filtering)."""
    if min_change is None and max_change is None:
        return coins
    out = []
    for c in coins:
        ch = c.get("change_24h")
        if ch is None:
            continue
        if min_change is not None and ch < min_change:
            continue
        if max_change is not None and ch > max_change:
            continue
        out.append(c)
    return out


def save_outputs(coins: list[dict]) -> None:
    os.makedirs(DATA_DIR, exist_ok=True)
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")

    # Latest snapshot -> JSON (consumed by the Flask API / dashboard)
    payload = {"updated_at": now, "coins": coins}
    with open(LATEST_JSON, "w") as f:
        json.dump(payload, f, indent=2)

    # Historical log -> CSV (append, for trend tracking)
    file_exists = os.path.isfile(HISTORY_CSV)
    with open(HISTORY_CSV, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        if not file_exists:
            writer.writeheader()
        for c in coins:
            writer.writerow({"timestamp": now, **c})

    print(f"[{now}] saved {len(coins)} coins -> {LATEST_JSON} and {HISTORY_CSV}")


def run_once(top_n: int, headless: bool, min_change=None, max_change=None) -> list[dict]:
    driver = build_driver(headless)
    try:
        coins = scrape_top_coins(driver, top_n)
        coins = filter_coins(coins, min_change, max_change)
        save_outputs(coins)
        return coins
    finally:
        driver.quit()


def main():
    parser = argparse.ArgumentParser(description="Scrape top cryptocurrencies from CoinMarketCap.")
    parser.add_argument("--headless", action="store_true", help="Run Chrome without a visible window.")
    parser.add_argument("--top", type=int, default=15, help="Number of coins to scrape (default 15).")
    parser.add_argument("--loop", type=int, default=0, help="Repeat every N seconds (0 = run once).")
    parser.add_argument("--min-change", type=float, default=None, help="Only keep coins with 24h change >= this.")
    parser.add_argument("--max-change", type=float, default=None, help="Only keep coins with 24h change <= this.")
    args = parser.parse_args()

    if args.loop and args.loop > 0:
        print(f"Looping every {args.loop}s. Ctrl+C to stop.")
        while True:
            try:
                run_once(args.top, args.headless, args.min_change, args.max_change)
            except Exception as exc:  # noqa: BLE001
                print(f"scrape failed: {exc}")
            time.sleep(args.loop)
    else:
        run_once(args.top, args.headless, args.min_change, args.max_change)


if __name__ == "__main__":
    main()
