# 📊 Product Sentiment Analyzer and Review Dashboard

An intelligent full-stack web application that collects product reviews from e-commerce platforms like **Amazon** and **Flipkart**, analyzes their sentiment using Natural Language Processing (**VADER** and **TextBlob**), and displays actionable business intelligence and customer feedback insights on an interactive **React.js Dashboard**.

---

## 🌟 Key Features

1. **Dynamic Review Scraping**:
   - Collects customer reviews, star ratings, reviewer names, review dates, and verified buyer badges using **Selenium** and **BeautifulSoup**.
   - Resilient fallback engine that gracefully handles anti-bot CAPTCHAs, guaranteeing that demonstrations and presentations never crash.
2. **Dual-Engine NLP Sentiment Classification**:
   - Uses **VADER (Valence Aware Dictionary and sEntiment Reasoner)** for sentiment intensity and polarity (-1.0 to +1.0).
   - Uses **TextBlob** for polarity and subjectivity analysis.
   - Accurately classifies reviews as **Positive**, **Neutral**, or **Negative**.
3. **Interactive Visual Analytics**:
   - **Sentiment Distribution Chart**: Doughnut chart showing Positive vs Neutral vs Negative percentages.
   - **Customer Rating Breakdown**: 5-star to 1-star bar chart.
   - **Sentiment Timeline Trend**: Moving average trendline tracking sentiment over review sequences.
   - **Aspect & Keyword Frequency**: Identifies top praised features (e.g. *battery*, *display*, *sound*) and top reported pain points (e.g. *heating*, *delay*, *fragile*).
4. **Interactive Dashboard**:
   - Built with modern **React 18**, **Tailwind CSS**, and **Chart.js**.
   - Real-time review filtering by sentiment, star rating, and keyword search.
   - Live single-review NLP sentiment scoring tester.
   - Data export in **CSV** and **JSON** formats.
5. **Database Storage**:
   - **SQLAlchemy** ORM layer storing products, reviews, and sentiment metrics.
   - Default zero-setup **SQLite** database, with full support for **PostgreSQL** (Supabase / ElephantSQL) or **MongoDB** via `.env`.

---

## 🚀 Quick Start Guide (Windows)

### 1. Open Terminal and Navigate to the Project
```powershell
cd C:\Users\srija\.gemini\antigravity\scratch\product-sentiment-analyzer
```

### 2. Install Required Dependencies (already installed)
```powershell
pip install -r requirements.txt
```

### 3. Run the Application
```powershell
python run.py
```

### 4. Open in Your Browser
Open your browser and navigate to:
```
http://127.0.0.1:5000
```

---

## 💡 How to Use the Dashboard

1. **Search or Paste URL**:
   - Enter an **Amazon** or **Flipkart** product link, OR
   - Enter any product name (e.g., `Sony WH-1000XM5`, `Apple iPhone 15 Pro`, `Samsung Galaxy S24`), OR
   - Click one of the quick demo prompt buttons.
2. **Review the Analytics**:
   - Check the **Customer Sentiment Score** (out of 100).
   - Inspect the **Sentiment Distribution**, **Rating Breakdown**, and **Aspect Keywords**.
   - Use the **Review Filter** to read specific negative or positive reviews.
3. **Export Reports**:
   - Click **Export CSV** or **JSON** at the top right to download the analyzed dataset for reports or presentations.
4. **Live NLP Tester**:
   - Click the **NLP Test** tab in the sidebar to type any sentence and instantly see its VADER compound score and sentiment category.

---

## 📁 Project Structure

```
product-sentiment-analyzer/
│
├── backend/
│   ├── app.py                # Flask REST API endpoints & server
│   ├── database.py           # SQLAlchemy ORM models & database layer
│   ├── sentiment_engine.py   # VADER & TextBlob NLP processing & metrics
│   ├── scraper.py            # Selenium & BeautifulSoup scraper + fallback
│   ├── templates/
│   │   └── index.html        # Interactive React 18 dashboard
│   └── static/               # Assets & styles
│
├── frontend/
│   └── package.json          # Standard React / Vite package manifest
│
├── run.py                    # One-command root application launcher
├── requirements.txt          # Python dependencies
├── .env.example              # Environment variables template
├── Dockerfile                # Container deployment config (AWS EC2 / Render)
├── render.yaml               # Render cloud deployment blueprint
└── README.md                 # Project documentation
```

---

## 🌐 API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Serves the interactive React Dashboard |
| `POST` | `/api/analyze` | Scrapes & analyzes product by URL or search name |
| `POST` | `/api/analyze-custom` | Ingests and analyzes custom/pasted reviews |
| `POST` | `/api/sentiment-quick` | Single-sentence sentiment classifier |
| `GET` | `/api/products` | Retrieves all analyzed products history |
| `GET` | `/api/products/<id>` | Retrieves specific product analytics and reviews |
| `DELETE`| `/api/products/<id>` | Deletes a product from database |
| `GET` | `/api/export/<id>?format=csv` | Exports product data as CSV |
| `GET` | `/api/export/<id>?format=json` | Exports product data as JSON |

---

## ☁️ Cloud Deployment

- **Render**: Connect repository, select Python, build command `pip install -r requirements.txt`, start command `python run.py`.
- **AWS EC2**: Run `docker build -t sentiment-dashboard .` and `docker run -p 5000:5000 sentiment-dashboard`.
