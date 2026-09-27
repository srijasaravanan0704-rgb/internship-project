import sys
import os
import unittest

# Add backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from sentiment_engine import analyze_single_review, process_and_aggregate_reviews, extract_aspect_keywords
from database import init_db, save_product_analysis, get_all_products, get_product_by_id, delete_product
from app import app

class TestProductSentimentAnalyzer(unittest.TestCase):

    def setUp(self):
        # Use an in-memory or temporary SQLite database for testing
        self.db_engine = init_db("sqlite:///:memory:")
        self.client = app.test_client()

    def test_sentiment_classification(self):
        """Test NLP sentiment classification accuracy with VADER and TextBlob."""
        pos = analyze_single_review("This phone is absolutely fantastic! Brilliant camera and battery life.")
        self.assertEqual(pos["sentiment_label"], "positive")
        self.assertGreater(pos["vader_compound"], 0.2)

        neg = analyze_single_review("Terrible product. Battery drains fast and overheats horribly. Total waste of money.")
        self.assertEqual(neg["sentiment_label"], "negative")
        self.assertLess(neg["vader_compound"], -0.2)

        neu = analyze_single_review("The package contains a power cable and documentation.", rating=3.0)
        self.assertEqual(neu["sentiment_label"], "neutral")

    def test_aggregation_and_aspect_extraction(self):
        """Test summary metrics and aspect keyword extraction."""
        sample_reviews = [
            {"author": "User A", "rating": 5.0, "review_text": "Exceptional battery life and fast charging display.", "review_date": "Today"},
            {"author": "User B", "rating": 1.0, "review_text": "Battery heating and defective screen display.", "review_date": "Yesterday"},
            {"author": "User C", "rating": 5.0, "review_text": "Great battery and beautiful camera.", "review_date": "2 days ago"}
        ]
        analyzed, summary, analytics = process_and_aggregate_reviews(sample_reviews)
        self.assertEqual(summary["total_reviews"], 3)
        self.assertIn("positive_percentage", summary)
        self.assertIn("keywords", analytics)
        self.assertTrue(len(analytics["keywords"]["positive_keywords"]) > 0)

    def test_database_crud(self):
        """Test database storage and retrieval."""
        meta = {"name": "Test Wireless Earbuds", "platform": "Amazon", "price": "$99"}
        sample_reviews = [
            {"author": "John", "rating": 5.0, "title": "Great sound", "review_text": "Love the deep bass.", "review_date": "Today"}
        ]
        analyzed, summary, _ = process_and_aggregate_reviews(sample_reviews)
        product = save_product_analysis(meta, analyzed, summary)

        self.assertIsNotNone(product["id"])
        self.assertEqual(product["name"], "Test Wireless Earbuds")

        # Test retrieve
        retrieved = get_product_by_id(product["id"])
        self.assertIsNotNone(retrieved)
        self.assertEqual(len(retrieved["reviews"]), 1)

        # Test delete
        deleted = delete_product(product["id"])
        self.assertTrue(deleted)
        self.assertIsNone(get_product_by_id(product["id"]))

    def test_api_endpoints(self):
        """Test Flask REST APIs."""
        # 1. Health check
        res = self.client.get("/api/health")
        self.assertEqual(res.status_code, 200)

        # 2. Quick sentiment API
        res = self.client.post("/api/sentiment-quick", json={"text": "Super fast shipping and great quality!"})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["sentiment_label"], "positive")

        # 3. Custom review analysis API
        res = self.client.post("/api/analyze-custom", json={
            "product_name": "API Test Laptop",
            "reviews": [
                {"review_text": "Awesome performance, super fast!", "rating": 5.0},
                {"review_text": "Keyboard keys get stuck, disappointing.", "rating": 2.0}
            ]
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])
        product_id = data["product"]["id"]

        # 4. Export CSV API
        res = self.client.get(f"/api/export/{product_id}?format=csv")
        self.assertEqual(res.status_code, 200)
        self.assertIn("text/csv", res.content_type)

if __name__ == "__main__":
    unittest.main()
