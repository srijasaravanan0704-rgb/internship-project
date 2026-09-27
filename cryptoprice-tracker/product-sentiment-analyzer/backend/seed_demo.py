import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import init_db, save_product_analysis, get_all_products
from scraper import scrape_product_reviews
from sentiment_engine import process_and_aggregate_reviews

def seed():
    init_db()
    existing = get_all_products()
    if existing:
        print(f"Database already contains {len(existing)} products. Skipping seed.")
        return

    demos = [
        ("Sony WH-1000XM5 Wireless Noise Cancelling Headphones", "Amazon"),
        ("Apple iPhone 15 Pro (128 GB)", "Flipkart")
    ]

    for name, platform in demos:
        print(f"Populating demo dataset for: {name} ({platform})...")
        res = scrape_product_reviews(name, max_reviews=15)
        analyzed_reviews, summary, _ = process_and_aggregate_reviews(res["reviews"])
        res["product"]["platform"] = platform
        save_product_analysis(res["product"], analyzed_reviews, summary)

    print("Demo dataset seeded successfully!")

if __name__ == "__main__":
    seed()
