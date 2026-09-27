import os
from datetime import datetime, timezone
from sqlalchemy import create_engine, Column, Integer, String, Float, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

Base = declarative_base()

def get_utc_now():
    return datetime.now(timezone.utc)

class Product(Base):
    __tablename__ = 'products'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    platform = Column(String(50), default="Generic")
    url = Column(Text, nullable=True)
    image_url = Column(Text, nullable=True)
    price = Column(String(50), nullable=True)
    total_reviews = Column(Integer, default=0)
    avg_rating = Column(Float, default=0.0)
    sentiment_score = Column(Float, default=0.0)
    positive_percentage = Column(Float, default=0.0)
    neutral_percentage = Column(Float, default=0.0)
    negative_percentage = Column(Float, default=0.0)
    created_at = Column(DateTime, default=get_utc_now)

    reviews = relationship('Review', back_populates='product', cascade='all, delete-orphan')

    def to_dict(self, include_reviews=False):
        data = {
            "id": self.id,
            "name": self.name,
            "platform": self.platform,
            "url": self.url,
            "image_url": self.image_url,
            "price": self.price,
            "total_reviews": self.total_reviews,
            "avg_rating": round(self.avg_rating, 2) if self.avg_rating else 0.0,
            "sentiment_score": round(self.sentiment_score, 2) if self.sentiment_score else 0.0,
            "positive_percentage": round(self.positive_percentage, 1),
            "neutral_percentage": round(self.neutral_percentage, 1),
            "negative_percentage": round(self.negative_percentage, 1),
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else None
        }
        if include_reviews:
            data["reviews"] = [r.to_dict() for r in self.reviews]
        return data


class Review(Base):
    __tablename__ = 'reviews'

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey('products.id', ondelete='CASCADE'), nullable=False)
    author = Column(String(100), default="Anonymous")
    rating = Column(Float, default=0.0)
    title = Column(String(255), default="")
    review_text = Column(Text, nullable=False)
    review_date = Column(String(50), default="")
    verified = Column(Boolean, default=True)
    sentiment_label = Column(String(20), default="neutral") # positive, neutral, negative
    polarity = Column(Float, default=0.0)
    subjectivity = Column(Float, default=0.0)
    vader_compound = Column(Float, default=0.0)
    created_at = Column(DateTime, default=get_utc_now)

    product = relationship('Product', back_populates='reviews')

    def to_dict(self):
        return {
            "id": self.id,
            "product_id": self.product_id,
            "author": self.author,
            "rating": self.rating,
            "title": self.title,
            "review_text": self.review_text,
            "review_date": self.review_date,
            "verified": self.verified,
            "sentiment_label": self.sentiment_label,
            "polarity": round(self.polarity, 3),
            "subjectivity": round(self.subjectivity, 3),
            "vader_compound": round(self.vader_compound, 3),
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else None
        }


# Database session management
_engine = None
_SessionFactory = None

def get_db_url():
    """Retrieve database URL from environment or default to SQLite file in project root."""
    env_url = os.environ.get("DATABASE_URL")
    if env_url:
        return env_url
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_path = os.path.join(base_dir, "sentiment_analyzer.db").replace("\\", "/")
    return f"sqlite:///{db_path}"

def init_db(db_url=None):
    """Initializes the database and creates tables if they don't exist."""
    global _engine, _SessionFactory
    url = db_url or get_db_url()
    
    # Handle render/heroku postgres url prefix fix if needed
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
        
    connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
    _engine = create_engine(url, connect_args=connect_args)
    Base.metadata.create_all(_engine)
    _SessionFactory = sessionmaker(bind=_engine)
    return _engine

def get_session():
    """Returns a new database session."""
    global _SessionFactory
    if _SessionFactory is None:
        init_db()
    return _SessionFactory()

def save_product_analysis(product_meta, reviews_list, summary_metrics):
    """
    Saves product and analyzed reviews into the database.
    Returns the created Product instance as dict.
    """
    session = get_session()
    try:
        product = Product(
            name=product_meta.get("name", "Unknown Product"),
            platform=product_meta.get("platform", "Generic"),
            url=product_meta.get("url", ""),
            image_url=product_meta.get("image_url", ""),
            price=product_meta.get("price", ""),
            total_reviews=summary_metrics.get("total_reviews", len(reviews_list)),
            avg_rating=summary_metrics.get("avg_rating", 0.0),
            sentiment_score=summary_metrics.get("overall_sentiment_score", 0.0),
            positive_percentage=summary_metrics.get("positive_percentage", 0.0),
            neutral_percentage=summary_metrics.get("neutral_percentage", 0.0),
            negative_percentage=summary_metrics.get("negative_percentage", 0.0)
        )
        session.add(product)
        session.flush() # Flush to populate product.id

        for rev in reviews_list:
            review_entry = Review(
                product_id=product.id,
                author=rev.get("author", "Verified Customer"),
                rating=float(rev.get("rating", 0.0)),
                title=rev.get("title", ""),
                review_text=rev.get("review_text", ""),
                review_date=rev.get("review_date", ""),
                verified=bool(rev.get("verified", True)),
                sentiment_label=rev.get("sentiment_label", "neutral"),
                polarity=float(rev.get("polarity", 0.0)),
                subjectivity=float(rev.get("subjectivity", 0.0)),
                vader_compound=float(rev.get("vader_compound", 0.0))
            )
            session.add(review_entry)

        session.commit()
        return product.to_dict(include_reviews=True)
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()

def get_all_products():
    session = get_session()
    try:
        products = session.query(Product).order_by(Product.created_at.desc()).all()
        return [p.to_dict(include_reviews=False) for p in products]
    finally:
        session.close()

def get_product_by_id(product_id):
    session = get_session()
    try:
        product = session.query(Product).filter(Product.id == product_id).first()
        if product:
            return product.to_dict(include_reviews=True)
        return None
    finally:
        session.close()

def delete_product(product_id):
    session = get_session()
    try:
        product = session.query(Product).filter(Product.id == product_id).first()
        if product:
            session.delete(product)
            session.commit()
            return True
        return False
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()
