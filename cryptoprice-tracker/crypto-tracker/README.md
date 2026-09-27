# Ledger — Live Cryptocurrency Price Tracker

A Selenium-powered crypto dashboard: scrapes the top 15 coins from CoinMarketCap,
serves them through a small Flask API, and renders them in a dark, custom-themed
dashboard with sorting, search, watchlists, price alerts, sparkline trends, and
a custom "Market Pulse" sentiment index.

## What's inside

```
crypto-tracker/
├── scraper.py            # Selenium scraper (the core project brief)
├── app.py                # Flask API + optional background auto-scrape
├── seed_sample_data.py   # generates realistic demo data (no browser needed)
├── requirements.txt
├── data/
│   ├── latest.json       # most recent snapshot (dashboard reads this)
│   └── history.csv       # timestamped log of every scrape (trend charts)
├── templates/index.html  # dashboard markup
└── static/
    ├── css/style.css     # dark theme
    └── js/dashboard.js   # fetch, render, sort/filter/search, alerts
```

## 1. Install

```bash
python -m venv venv
source venv/bin/activate        # venv\Scripts\activate on Windows
pip install -r requirements.txt
```

You need Google Chrome installed. `webdriver_manager` downloads the matching
ChromeDriver automatically the first time you run the scraper — no manual
driver setup.

## 2. Try it instantly with sample data (no Selenium needed)

```bash
python seed_sample_data.py     # writes data/latest.json + data/history.csv
python app.py
```

Open **http://127.0.0.1:5000** — the dashboard, table, sparklines, and Market
Pulse gauge all work immediately on the generated sample data. This is the
fastest way to demo the UI (e.g. in an interview) without depending on
CoinMarketCap being reachable at that moment.

## 3. Run the real scraper

```bash
python scraper.py                 # one scrape, visible Chrome window
python scraper.py --headless      # one scrape, no window
python scraper.py --loop 300      # re-scrape every 5 minutes, forever
```

This overwrites `data/latest.json` and appends to `data/history.csv`. Refresh
the dashboard (or just wait — it auto-refreshes every 60s) to see live data.

To have Flask itself keep the data fresh in the background instead of running
the scraper separately:

```bash
python app.py --auto-scrape --interval 300
```

## Features

**From the original brief**
- Selenium scraping of top-N (default 15) coins: name, price, 1h/24h/7d change, market cap, volume
- Headless mode, CSV export, timestamped historical logging, threshold filtering (`--min-change` / `--max-change`)

**Added for the dashboard**
- Flask REST API (`/api/coins`, `/api/coin/<symbol>/history`, `/api/export.csv`, `/api/status`)
- Dark, custom-designed UI (not a template) with sortable/searchable/filterable table
- Per-coin sparklines and a full focus chart built from the actual history log
- A custom **Market Pulse** index — a market-cap-weighted 24h sentiment score (0–100), computed server-side, distinct from just re-displaying CoinMarketCap's own numbers
- Watchlist (persisted in the browser via `localStorage`)
- Price alerts with browser notifications, checked on every refresh
- One-click CSV export straight from the UI
- Fully responsive layout down to mobile

## Notes on the scraper

CoinMarketCap's markup changes periodically and it can rate-limit or challenge
obvious bots. `scraper.py` sets a real user-agent, hides the `navigator.webdriver`
flag, and scrolls the page to trigger lazy-loaded rows — but if CoinMarketCap
changes its table structure, you may need to adjust the CSS selectors in
`scrape_top_coins()`. Wrapping each row in try/except means one broken row
won't kill the whole scrape.
