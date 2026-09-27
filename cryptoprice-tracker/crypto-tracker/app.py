"""
Cryptocurrency Price Tracker — Backend
----------------------------------------
Serves the scraped data (data/latest.json, data/history.csv) to the
dashboard frontend, and optionally re-runs the Selenium scraper on a
schedule in a background thread.

Run:
    python app.py                # serves data/latest.json as-is
    python app.py --auto-scrape  # also re-scrapes every SCRAPE_INTERVAL seconds
"""

import argparse
import csv
import json
import os
import threading
import time
from datetime import datetime, timezone

from flask import Flask, jsonify, request, send_file, Response

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
LATEST_JSON = os.path.join(DATA_DIR, "latest.json")
HISTORY_CSV = os.path.join(DATA_DIR, "history.csv")
SCRAPE_INTERVAL = 300  # seconds

app = Flask(__name__, static_folder="static", template_folder="templates")


def load_latest():
    if not os.path.isfile(LATEST_JSON):
        return {"updated_at": None, "coins": []}
    with open(LATEST_JSON) as f:
        return json.load(f)


def market_pulse(coins):
    """
    A small custom index (not just copied from CoinMarketCap): a
    market-cap-weighted average of 24h change, scaled 0-100 like a
    sentiment gauge. >55 = bullish tilt, <45 = bearish tilt.
    """
    total_cap = sum(c.get("market_cap") or 0 for c in coins)
    if not total_cap:
        return 50
    weighted = sum((c.get("change_24h") or 0) * (c.get("market_cap") or 0) for c in coins)
    avg_change = weighted / total_cap
    # squash the average % change into a 0-100 band, centered on 50
    score = 50 + (avg_change * 4)
    return max(0, min(100, round(score, 1)))


@app.route("/")
def index():
    return app.send_static_file("index.html") if os.path.isfile(
        os.path.join(app.static_folder, "index.html")
    ) else send_file(os.path.join(BASE_DIR, "templates", "index.html"))


@app.route("/api/coins")
def api_coins():
    data = load_latest()
    coins = data.get("coins", [])

    q = request.args.get("q", "").lower()
    sort_by = request.args.get("sort", "rank")
    order = request.args.get("order", "asc")

    if q:
        coins = [c for c in coins if q in c["name"].lower() or q in c["symbol"].lower()]

    if sort_by in {"rank", "price", "change_1h", "change_24h", "change_7d", "market_cap", "volume_24h"}:
        coins = sorted(coins, key=lambda c: (c.get(sort_by) is None, c.get(sort_by)),
                        reverse=(order == "desc"))

    return jsonify({
        "updated_at": data.get("updated_at"),
        "count": len(coins),
        "market_pulse": market_pulse(data.get("coins", [])),
        "coins": coins,
    })


@app.route("/api/coin/<symbol>/history")
def api_coin_history(symbol):
    """Returns the historical price log for one coin, for sparkline charts."""
    symbol = symbol.upper()
    points = []
    if os.path.isfile(HISTORY_CSV):
        with open(HISTORY_CSV) as f:
            for row in csv.DictReader(f):
                if row["symbol"].upper() == symbol:
                    points.append({"t": row["timestamp"], "price": float(row["price"] or 0)})
    return jsonify(points[-100:])


@app.route("/api/export.csv")
def export_csv():
    if not os.path.isfile(HISTORY_CSV):
        return Response("No data yet — run the scraper first.", mimetype="text/plain")
    return send_file(HISTORY_CSV, as_attachment=True, download_name="crypto_history.csv")


@app.route("/api/status")
def api_status():
    data = load_latest()
    return jsonify({
        "updated_at": data.get("updated_at"),
        "coin_count": len(data.get("coins", [])),
        "has_history": os.path.isfile(HISTORY_CSV),
    })


def background_scraper(interval: int):
    from scraper import run_once  # imported lazily so `python app.py` works w/o selenium installed
    while True:
        try:
            print(f"[auto-scrape] running… ({datetime.now(timezone.utc).isoformat(timespec='seconds')})")
            run_once(top_n=15, headless=True)
        except Exception as exc:  # noqa: BLE001
            print(f"[auto-scrape] failed: {exc}")
        time.sleep(interval)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--auto-scrape", action="store_true", help="Re-scrape on a background timer.")
    parser.add_argument("--interval", type=int, default=SCRAPE_INTERVAL)
    parser.add_argument("--port", type=int, default=5000)
    parser.add_argument("--debug", action="store_true", help="Enable Flask debug/auto-reload.")
    args = parser.parse_args()

    if args.auto_scrape:
        t = threading.Thread(target=background_scraper, args=(args.interval,), daemon=True)
        t.start()

    app.run(debug=args.debug, port=args.port)
