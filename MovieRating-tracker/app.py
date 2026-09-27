import os
import csv
import io
from flask import Flask, render_template, jsonify, request, send_file
from flask_cors import CORS
from scraper import run_scraper, load_from_csv, save_to_csv, CSV_FILEPATH

app = Flask(__name__)
CORS(app)

# Ensure CSV exists at app startup
if not os.path.exists(CSV_FILEPATH):
    run_scraper(use_selenium=False, save_csv_file=True)

def compute_stats(movies):
    """Compute aggregate analytics from movies list."""
    if not movies:
        return {
            "total_movies": 0,
            "avg_rating": 0.0,
            "top_movie": "N/A",
            "top_rating": 0.0,
            "decades": {}
        }

    total = len(movies)
    ratings = []
    top_movie = movies[0]
    decades = {}

    for m in movies:
        try:
            r = float(m.get("IMDb Rating", 0))
            ratings.append(r)
            if r > float(top_movie.get("IMDb Rating", 0)):
                top_movie = m
        except (ValueError, TypeError):
            pass

        year = str(m.get("Release Year", "")).strip()
        if year.isdigit() and len(year) == 4:
            decade = f"{year[:3]}0s"
            decades[decade] = decades.get(decade, 0) + 1

    avg_rating = round(sum(ratings) / len(ratings), 2) if ratings else 0.0

    return {
        "total_movies": total,
        "avg_rating": avg_rating,
        "top_movie": top_movie.get("Title", "N/A"),
        "top_rating": top_movie.get("IMDb Rating", 0.0),
        "decades": dict(sorted(decades.items()))
    }

@app.route("/")
def index():
    """Render main web application dashboard."""
    return render_template("index.html")

@app.route("/api/movies", methods=["GET"])
def get_movies():
    """Get all movies stored in CSV file."""
    movies = load_from_csv(CSV_FILEPATH)
    if not movies:
        movies = run_scraper(use_selenium=False, save_csv_file=True)
    return jsonify({"status": "success", "count": len(movies), "movies": movies})

@app.route("/api/scrape", methods=["POST"])
def trigger_scrape():
    """Trigger dynamic movie scraping."""
    data = request.get_json(silent=True) or {}
    use_selenium = data.get("use_selenium", False)
    movies = run_scraper(use_selenium=use_selenium, save_csv_file=True)
    return jsonify({
        "status": "success",
        "message": f"Successfully scraped {len(movies)} movies",
        "count": len(movies),
        "movies": movies
    })

@app.route("/api/stats", methods=["GET"])
def get_stats():
    """Get movie dataset aggregate statistics."""
    movies = load_from_csv(CSV_FILEPATH)
    stats = compute_stats(movies)
    return jsonify({"status": "success", "stats": stats})

@app.route("/api/download-csv", methods=["GET"])
def download_csv():
    """Download the generated IMDb movies CSV file."""
    if not os.path.exists(CSV_FILEPATH):
        run_scraper(use_selenium=False, save_csv_file=True)
    return send_file(
        CSV_FILEPATH,
        mimetype="text/csv",
        as_attachment=True,
        download_name="imdb_top_movies.csv"
    )

@app.route("/api/upload-csv", methods=["POST"])
def upload_csv():
    """Upload custom CSV file and parse movie data."""
    if "file" not in request.files:
        return jsonify({"status": "error", "message": "No file uploaded"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"status": "error", "message": "No file selected"}), 400

    if not file.filename.endswith(".csv"):
        return jsonify({"status": "error", "message": "Only CSV files are allowed"}), 400

    try:
        stream = io.StringIO(file.stream.read().decode("utf-8"), newline=None)
        reader = csv.DictReader(stream)
        
        movies = []
        for idx, row in enumerate(reader, 1):
            movies.append({
                "Rank": row.get("Rank", idx),
                "Title": row.get("Title", row.get("title", row.get("Movie", "Unknown"))),
                "Release Year": row.get("Release Year", row.get("Year", row.get("year", "N/A"))),
                "IMDb Rating": float(row.get("IMDb Rating", row.get("Rating", row.get("rating", 0.0)))),
                "Votes": row.get("Votes", row.get("votes", "N/A")),
                "Poster Image": row.get("Poster Image", row.get("Poster", "")),
                "IMDb Link": row.get("IMDb Link", row.get("URL", "#"))
            })

        if movies:
            save_to_csv(movies, CSV_FILEPATH)
            return jsonify({
                "status": "success",
                "message": f"Successfully imported {len(movies)} movies from CSV file.",
                "count": len(movies),
                "movies": movies
            })
        else:
            return jsonify({"status": "error", "message": "Uploaded CSV file contained no valid movie rows."}), 400

    except Exception as e:
        return jsonify({"status": "error", "message": f"Error parsing CSV file: {str(e)}"}), 500

if __name__ == "__main__":
    print("[+] Starting IMDb Scraper & Web App Server at http://127.0.0.1:5000...")
    app.run(host="127.0.0.1", port=5000, debug=True)
