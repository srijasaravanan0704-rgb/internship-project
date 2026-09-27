import re
from collections import Counter
import statistics
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from textblob import TextBlob

# Initialize VADER
analyzer = SentimentIntensityAnalyzer()

# Curated domain-specific stopwords for e-commerce review keyword extraction
STOPWORDS = set([
    'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of',
    'with', 'by', 'from', 'up', 'about', 'into', 'over', 'after', 'is', 'am',
    'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do',
    'does', 'did', 'i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'you',
    'your', 'yours', 'he', 'him', 'his', 'she', 'her', 'it', 'its', 'they',
    'them', 'their', 'what', 'which', 'who', 'this', 'that', 'these', 'those',
    'then', 'so', 'than', 'too', 'very', 'can', 'will', 'just', 'should',
    'now', 'also', 'product', 'item', 'amazon', 'flipkart', 'buy', 'bought',
    'one', 'get', 'got', 'day', 'days', 'use', 'using', 'used', 'really',
    'would', 'much', 'even', 'like', 'good', 'bad' # Filter out pure generic words from aspects
])

COMMON_NAMES = {
    'john', 'srijan', 'alice', 'bob', 'david', 'michael', 'sarah', 'priya', 'rohan',
    'rahul', 'amit', 'ananya', 'vikram', 'emily', 'alex', 'chris', 'grace', 'joy',
    'frank', 'sunny', 'miles', 'guy', 'mark', 'grant', 'rich', 'will', 'bill', 'steve',
    'james', 'robert', 'mary', 'jessica', 'patricia', 'jennifer', 'linda', 'elizabeth',
    'barbara', 'susan', 'joseph', 'thomas', 'charles', 'christopher', 'daniel', 'matthew',
    'anthony', 'donald', 'paul', 'steven', 'andrew', 'kenneth', 'joshua', 'george',
    'kevin', 'brian', 'edward', 'ronald', 'timothy', 'jason', 'jeffrey', 'ryan', 'jacob',
    'gary', 'nicholas', 'eric', 'jonathan', 'stephen', 'larry', 'justin', 'scott', 'brandon',
    'benjamin', 'samuel', 'gregory', 'alexander', 'raymond', 'patrick', 'jack',
    'dennis', 'jerry', 'tyler', 'aaron', 'jose', 'adam', 'henry', 'nathan', 'douglas', 'zachary',
    'peter', 'kyle', 'walter', 'ethan', 'jeremy', 'harold', 'keith', 'christian', 'roger',
    'noah', 'gerald', 'carl', 'terry', 'sean', 'austin', 'arthur', 'lawrence', 'jesse',
    'dylan', 'bryan', 'joe', 'jordan', 'billy', 'bruce', 'albert', 'willie', 'gabriel',
    'logan', 'alan', 'juan', 'wayne', 'roy', 'ralph', 'randy', 'eugene', 'vincent', 'russell',
    'louis', 'philip', 'bobby', 'johnny', 'bradley', 'sneha', 'arun', 'karthik', 'deepak',
    'pooja', 'neha', 'rajesh', 'suresh', 'ramesh', 'vince', 'sharma', 'nair', 'patel', 'kumar'
}

OPINION_WORDS = {
    'good', 'bad', 'great', 'terrible', 'awesome', 'horrible', 'worst', 'best', 'love', 'hate',
    'disappointed', 'disappointing', 'excellent', 'superb', 'flawless', 'defective', 'broken',
    'happy', 'satisfied', 'unsatisfied', 'poor', 'amazing', 'brilliant', 'wonderful', 'trash',
    'garbage', 'waste', 'worth', 'value', 'cheap', 'expensive', 'useful', 'useless', 'slow',
    'fast', 'heating', 'lag', 'battery', 'screen', 'display', 'camera', 'sound', 'audio',
    'noise', 'build', 'quality', 'sturdy', 'fragile', 'flimsy', 'durable', 'recommend',
    'recommended', 'recommending', 'buy', 'bought', 'purchase', 'scam', 'fake', 'original',
    'authentic', 'works', 'working', 'failed', 'failing', 'defect', 'issue', 'problem',
    'glitch', 'bug', 'drains', 'draining', 'sleek', 'smooth', 'laggy', 'clunky', 'nice'
}

def detect_entity_or_non_opinion(cleaned_text: str) -> tuple:
    """
    Checks if cleaned_text is a person's name, standalone entity, or non-opinion text.
    Returns: (is_entity_bool, entity_type_str, entity_note_str)
    """
    if not cleaned_text:
        return False, "", ""

    tokens = re.findall(r'\b[a-zA-Z0-9]+\b', cleaned_text)
    lower_tokens = [t.lower() for t in tokens]

    if not tokens:
        return True, "Non-Opinion Text", "No words or sentiment detected."

    # Check if text contains any explicit opinion indicator
    has_opinion_word = any(w in OPINION_WORDS for w in lower_tokens)

    # 1. Single or double word proper names or common names (e.g. "John", "Srijan", "John Smith", "Grace", "Sunny")
    if len(tokens) <= 3:
        is_name_match = any(w in COMMON_NAMES for w in lower_tokens)
        all_capitalized = all(t[0].isupper() for t in tokens if t.isalpha())

        if (is_name_match or (all_capitalized and len(tokens) <= 2)) and not has_opinion_word:
            return True, "Person Name / Entity", f"'{cleaned_text}' is identified as a name or proper entity without sentiment context."

    # 2. Text without opinion words and low word count (e.g., "Sony", "Apple iPhone", "Table", "12345")
    if len(tokens) <= 3 and not has_opinion_word:
        blob = TextBlob(cleaned_text)
        if abs(blob.sentiment.polarity) < 0.01 and blob.sentiment.subjectivity < 0.1:
            return True, "Non-Opinion Entity", f"'{cleaned_text}' is a noun or entity with no sentiment/opinion words."

    return False, "", ""

def clean_text(text: str) -> str:
    """Sanitizes review text by removing unwanted URLs and formatting artifacts."""
    if not text or not isinstance(text, str):
        return ""
    text = re.sub(r'http\S+|www\S+|https\S+', '', text, flags=re.MULTILINE)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def analyze_single_review(review_text: str, rating: float = 0.0) -> dict:
    """
    Analyzes sentiment of a single review using both VADER and TextBlob.
    Returns sentiment_label, vader_compound, polarity, and subjectivity.
    """
    cleaned = clean_text(review_text)
    if not cleaned:
        return {
            "sentiment_label": "neutral",
            "vader_compound": 0.0,
            "polarity": 0.0,
            "subjectivity": 0.0,
            "sentiment_scores": {"pos": 0.0, "neu": 1.0, "neg": 0.0, "compound": 0.0},
            "is_entity": True,
            "entity_type": "Empty Input",
            "entity_note": "No text provided for sentiment scoring."
        }

    # Check for person names or non-opinion entities
    is_entity, entity_type, entity_note = detect_entity_or_non_opinion(cleaned)
    if is_entity:
        return {
            "sentiment_label": "neutral",
            "vader_compound": 0.0,
            "polarity": 0.0,
            "subjectivity": 0.0,
            "sentiment_scores": {"pos": 0.0, "neu": 1.0, "neg": 0.0, "compound": 0.0},
            "is_entity": True,
            "entity_type": entity_type,
            "entity_note": entity_note
        }

    # 1. VADER analysis
    vader_scores = analyzer.polarity_scores(cleaned)
    compound = vader_scores['compound']

    # 2. TextBlob analysis
    blob = TextBlob(cleaned)
    polarity = blob.sentiment.polarity
    subjectivity = blob.sentiment.subjectivity

    # 3. Sentiment Classification Logic
    if compound >= 0.05:
        label = "positive"
    elif compound <= -0.05:
        label = "negative"
    else:
        # Borderline cases: consider star rating or TextBlob polarity
        if rating >= 4.0 or polarity > 0.15:
            label = "positive"
        elif (0.0 < rating <= 2.0) or polarity < -0.15:
            label = "negative"
        else:
            label = "neutral"

    return {
        "sentiment_label": label,
        "vader_compound": round(compound, 3),
        "polarity": round(polarity, 3),
        "subjectivity": round(subjectivity, 3),
        "sentiment_scores": vader_scores,
        "is_entity": False,
        "entity_type": "",
        "entity_note": ""
    }

def extract_aspect_keywords(reviews_list: list, top_n: int = 15) -> dict:
    """
    Extracts top keywords and feature mentions from reviews, split by positive and negative contexts.
    """
    pos_words = []
    neg_words = []
    all_words = []

    for rev in reviews_list:
        text = rev.get("review_text", "").lower()
        words = re.findall(r'\b[a-z]{3,}\b', text)
        filtered = [w for w in words if w not in STOPWORDS]
        
        all_words.extend(filtered)
        label = rev.get("sentiment_label", "neutral")
        if label == "positive":
            pos_words.extend(filtered)
        elif label == "negative":
            neg_words.extend(filtered)

    pos_counter = Counter(pos_words).most_common(top_n)
    neg_counter = Counter(neg_words).most_common(top_n)
    all_counter = Counter(all_words).most_common(top_n)

    return {
        "overall_keywords": [{"word": w, "count": c} for w, c in all_counter],
        "positive_keywords": [{"word": w, "count": c} for w, c in pos_counter],
        "negative_keywords": [{"word": w, "count": c} for w, c in neg_counter]
    }

def calculate_review_trends(reviews_list: list) -> list:
    """
    Computes sentiment trend over reviews sequence using rolling moving averages.
    """
    if not reviews_list:
        return []

    trends = []
    window = 3
    recent_compounds = []

    for i, r in enumerate(reviews_list):
        compound = float(r.get("vader_compound", 0.0))
        recent_compounds.append(compound)
        if len(recent_compounds) > window:
            recent_compounds.pop(0)

        smoothed = sum(recent_compounds) / len(recent_compounds)
        trends.append({
            "review_num": i + 1,
            "date": str(r.get("review_date") or f"Review #{i+1}"),
            "sentiment_score": round(compound, 2),
            "smoothed_sentiment": round(smoothed, 2),
            "rating": round(float(r.get("rating", 0.0)), 1)
        })

    return trends

def process_and_aggregate_reviews(reviews_raw: list) -> tuple:
    """
    Runs sentiment analysis on all reviews, aggregates metrics, generates trends & keywords.
    Returns: (analyzed_reviews, summary_metrics, visual_analytics)
    """
    if not reviews_raw:
        return [], {
            "total_reviews": 0,
            "avg_rating": 0.0,
            "overall_sentiment_score": 0.0,
            "positive_percentage": 0.0,
            "neutral_percentage": 0.0,
            "negative_percentage": 0.0,
            "positive_count": 0,
            "neutral_count": 0,
            "negative_count": 0,
            "rating_distribution": {5: 0, 4: 0, 3: 0, 2: 0, 1: 0}
        }, {"keywords": {}, "trends": []}

    analyzed_reviews = []
    pos_count = 0
    neu_count = 0
    neg_count = 0
    rating_counts = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    ratings = []
    compounds = []

    for rev in reviews_raw:
        raw_text = rev.get("review_text", "")
        raw_rating = float(rev.get("rating", 0.0))

        sentiment_res = analyze_single_review(raw_text, raw_rating)

        enriched_rev = dict(rev)
        enriched_rev["sentiment_label"] = sentiment_res["sentiment_label"]
        enriched_rev["polarity"] = sentiment_res["polarity"]
        enriched_rev["subjectivity"] = sentiment_res["subjectivity"]
        enriched_rev["vader_compound"] = sentiment_res["vader_compound"]

        # Track aggregates
        if enriched_rev["sentiment_label"] == "positive":
            pos_count += 1
        elif enriched_rev["sentiment_label"] == "negative":
            neg_count += 1
        else:
            neu_count += 1

        if raw_rating > 0:
            int_rating = int(round(raw_rating))
            if 1 <= int_rating <= 5:
                rating_counts[int_rating] += 1
            ratings.append(raw_rating)

        compounds.append(sentiment_res["vader_compound"])
        analyzed_reviews.append(enriched_rev)

    total = len(analyzed_reviews)
    avg_rating = (sum(ratings) / len(ratings)) if ratings else 0.0
    overall_sentiment = (sum(compounds) / len(compounds)) if compounds else 0.0

    pos_pct = round((pos_count / total) * 100, 1) if total > 0 else 0.0
    neu_pct = round((neu_count / total) * 100, 1) if total > 0 else 0.0
    neg_pct = round((neg_count / total) * 100, 1) if total > 0 else 0.0

    # Score mapped to 0-100 scale: (compound + 1) * 50
    normalized_score = round((overall_sentiment + 1.0) * 50.0, 1)

    summary_metrics = {
        "total_reviews": total,
        "avg_rating": round(avg_rating, 2),
        "overall_sentiment_score": round(overall_sentiment, 2),
        "normalized_score": normalized_score,
        "positive_percentage": pos_pct,
        "neutral_percentage": neu_pct,
        "negative_percentage": neg_pct,
        "positive_count": pos_count,
        "neutral_count": neu_count,
        "negative_count": neg_count,
        "rating_distribution": rating_counts
    }

    visual_analytics = {
        "keywords": extract_aspect_keywords(analyzed_reviews),
        "trends": calculate_review_trends(analyzed_reviews),
        "sentiment_distribution": {
            "labels": ["Positive", "Neutral", "Negative"],
            "counts": [pos_count, neu_count, neg_count],
            "percentages": [pos_pct, neu_pct, neg_pct]
        },
        "rating_breakdown": {
            "stars": ["5 Star", "4 Star", "3 Star", "2 Star", "1 Star"],
            "counts": [rating_counts[5], rating_counts[4], rating_counts[3], rating_counts[2], rating_counts[1]]
        }
    }

    return analyzed_reviews, summary_metrics, visual_analytics
