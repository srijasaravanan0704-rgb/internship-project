"""
Generates realistic-looking sample data (15 coins + 24h of history)
so the dashboard can be demoed immediately, without running Selenium
first. Delete data/*.json/csv once you've run the real scraper.
"""
import csv
import json
import os
import random
from datetime import datetime, timedelta, timezone

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

COINS = [
    ("Bitcoin", "BTC", 57626.63, 1.17e12),
    ("Ethereum", "ETH", 4295.08, 5.16e11),
    ("Tether", "USDT", 1.00, 1.20e11),
    ("BNB", "BNB", 612.34, 9.02e10),
    ("Solana", "SOL", 178.92, 8.44e10),
    ("XRP", "XRP", 1.42, 8.10e10),
    ("Dogecoin", "DOGE", 0.126, 1.83e10),
    ("Cardano", "ADA", 0.612, 2.15e10),
    ("Avalanche", "AVAX", 124.23, 1.90e10),
    ("Chainlink", "LINK", 26.12, 1.62e10),
    ("Polkadot", "DOT", 8.77, 1.14e10),
    ("Polygon", "MATIC", 0.98, 9.10e9),
    ("Litecoin", "LTC", 112.4, 8.40e9),
    ("TRON", "TRX", 0.181, 1.61e10),
    ("Toncoin", "TON", 6.84, 1.73e10),
]

CSV_FIELDS = [
    "timestamp", "rank", "name", "symbol", "price",
    "change_1h", "change_24h", "change_7d", "market_cap", "volume_24h",
]

random.seed(7)


def make_snapshot(base_prices, jitter=0.01):
    coins = []
    for i, (name, symbol, base_price, cap) in enumerate(base_prices, start=1):
        price = round(base_price * (1 + random.uniform(-jitter, jitter)), 6)
        coins.append({
            "rank": i,
            "name": name,
            "symbol": symbol,
            "price": price,
            "change_1h": round(random.uniform(-2, 2), 2),
            "change_24h": round(random.uniform(-8, 8), 2),
            "change_7d": round(random.uniform(-15, 20), 2),
            "market_cap": round(cap * (1 + random.uniform(-0.01, 0.01)), 2),
            "volume_24h": round(cap * random.uniform(0.03, 0.09), 2),
        })
    return coins


now = datetime.now(timezone.utc)

# 24 hourly history points per coin for sparklines/trend charts
history_rows = []
for hours_ago in range(24, 0, -1):
    ts = (now - timedelta(hours=hours_ago)).isoformat(timespec="seconds")
    snapshot = make_snapshot(COINS, jitter=0.03)
    for c in snapshot:
        history_rows.append({"timestamp": ts, **c})

# Latest snapshot
latest_coins = make_snapshot(COINS, jitter=0.01)
with open(os.path.join(DATA_DIR, "latest.json"), "w") as f:
    json.dump({"updated_at": now.isoformat(timespec="seconds"), "coins": latest_coins}, f, indent=2)

with open(os.path.join(DATA_DIR, "history.csv"), "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
    writer.writeheader()
    for row in history_rows:
        writer.writerow(row)
    for c in latest_coins:
        writer.writerow({"timestamp": now.isoformat(timespec="seconds"), **c})

print("Sample data written to data/latest.json and data/history.csv")
