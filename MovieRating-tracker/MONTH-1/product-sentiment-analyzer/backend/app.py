import os
import io
import csv
from flask import Flask, request, jsonify, render_template, send_from_directory, Response
from flask_cors import CORS

from database import init_db, save_product_analysis, get_all_products, get_product_by_id, delete_product
from sentiment_engine import process_and_aggregate_reviews, analyze_single_review
from scraper import scrape_product_reviews

# Define paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
STATIC_DIR = os.path.join(BASE_DIR, "static")

app = Flask(__name__, template_folder=TEMPLATES_DIR, static_folder=STATIC_DIR)
CORS(app)

# Initialize database
init_db()

@app.route("/")
def home():
    """Serves the interactive React Dashboard."""
    return render_template("index.html")

@app.route("/api/health", methods=["GET"])
def health_check():
    return jsonify({"status": "healthy", "service": "Product Sentiment Analyzer API"})

@app.route("/api/analyze", methods=["POST"])
def analyze_product():
    """
    Scrapes product reviews from Amazon/Flipkart URL or query,
    analyzes sentiments via NLP, saves to database, and returns analytics.
    """
    data = request.get_json() or {}
    target = data.get("url") or data.get("query") or data.get("product_name", "").strip()

    if not target:
        return jsonify({"error": "Product URL or search query is required."}), 400

    try:
        # Step 1: Scrape reviews
        scrape_result = scrape_product_reviews(target, max_reviews=data.get("max_reviews", 25))
        product_meta = scrape_result["product"]
        raw_reviews = scrape_result["reviews"]

        if not raw_reviews:
            return jsonify({"error": "No reviews could be found for this product."}), 404

        # Step 2: NLP Sentiment Analysis & Aggregation
        analyzed_reviews, summary_metrics, visual_analytics = process_and_aggregate_reviews(raw_reviews)

        # Step 3: Save to Database
        saved_product = save_product_analysis(product_meta, analyzed_reviews, summary_metrics)

        return jsonify({
            "success": True,
            "product": saved_product,
            "summary": summary_metrics,
            "analytics": visual_analytics,
            "reviews": analyzed_reviews,
            "note": product_meta.get("note", "")
        })

    except Exception as e:
        return jsonify({"error": f"Analysis failed: {str(e)}"}), 500

@app.route("/api/analyze-custom", methods=["POST"])
def analyze_custom_reviews():
    """
    Analyzes custom reviews provided directly by the user (or parsed from CSV).
    """
    data = request.get_json() or {}
    product_name = data.get("product_name", "Custom Analyzed Product").strip()
    raw_reviews = data.get("reviews", [])

    if not raw_reviews:
        return jsonify({"error": "At least one review text is required."}), 400

    try:
        analyzed_reviews, summary_metrics, visual_analytics = process_and_aggregate_reviews(raw_reviews)
        product_meta = {
            "name": product_name,
            "platform": "Custom Ingestion",
            "url": "",
            "image_url": "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=500&q=80",
            "price": "N/A"
        }
        saved_product = save_product_analysis(product_meta, analyzed_reviews, summary_metrics)

        return jsonify({
            "success": True,
            "product": saved_product,
            "summary": summary_metrics,
            "analytics": visual_analytics,
            "reviews": analyzed_reviews
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/sentiment-quick", methods=["POST"])
def quick_sentiment():
    """Quick NLP classification for a single sentence or review."""
    data = request.get_json() or {}
    text = data.get("text", "").strip()
    rating = float(data.get("rating", 0.0))

    if not text:
        return jsonify({"error": "Text is required"}), 400

    result = analyze_single_review(text, rating)
    return jsonify(result)

@app.route("/api/products", methods=["GET"])
def list_products():
    """Returns all historically analyzed products."""
    products = get_all_products()
    return jsonify({"products": products})

@app.route("/api/products/<int:product_id>", methods=["GET"])
def get_product(product_id):
    """Retrieves full details, recomputes analytics & returns reviews for a product."""
    product = get_product_by_id(product_id)
    if not product:
        return jsonify({"error": "Product not found"}), 404

    reviews = product.get("reviews", [])
    # Re-run aggregation for chart formats
    _, summary_metrics, visual_analytics = process_and_aggregate_reviews(reviews)

    return jsonify({
        "product": product,
        "summary": summary_metrics,
        "analytics": visual_analytics,
        "reviews": reviews
    })

@app.route("/api/products/<int:product_id>", methods=["DELETE"])
def remove_product(product_id):
    """Deletes a product from database."""
    success = delete_product(product_id)
    if success:
        return jsonify({"success": True, "message": "Product deleted successfully"})
    return jsonify({"error": "Product not found"}), 404

@app.route("/api/export/<int:product_id>", methods=["GET"])
def export_product_data(product_id):
    """Exports product reviews and sentiment analysis results as CSV or JSON."""
    export_format = request.args.get("format", "csv").lower()
    product = get_product_by_id(product_id)
    if not product:
        return jsonify({"error": "Product not found"}), 404

    reviews = product.get("reviews", [])

    if export_format == "json":
        return jsonify({
            "product": product,
            "reviews": reviews
        })

    # CSV Export
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Review ID", "Author", "Rating", "Review Title", "Review Text",
        "Sentiment Label", "VADER Compound", "Polarity", "Subjectivity", "Review Date"
    ])

    for r in reviews:
        writer.writerow([
            r.get("id"),
            r.get("author"),
            r.get("rating"),
            r.get("title"),
            r.get("review_text"),
            r.get("sentiment_label"),
            r.get("vader_compound"),
            r.get("polarity"),
            r.get("subjectivity"),
            r.get("review_date")
        ])

    filename = f"sentiment_report_{product_id}_{product['name'][:20].replace(' ', '_')}.csv"
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment;filename={filename}"}
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"🚀 Product Sentiment Analyzer server starting at http://127.0.0.1:{port}")
    app.run(host="0.0.0.0", port=port, debug=True)
