import os
import sys

# Ensure backend folder is in Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

from app import app

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print("=" * 65)
    print(" ⭐ Product Sentiment Analyzer & Review Dashboard")
    print(f" 🌐 Web Dashboard running at: http://127.0.0.1:{port}")
    print(" 🚀 Press Ctrl+C to stop the server")
    print("=" * 65)
    app.run(host="0.0.0.0", port=port, debug=True)
