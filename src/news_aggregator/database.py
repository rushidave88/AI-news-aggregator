

from sqlalchemy import create_engine, select, update
from sqlalchemy.orm import sessionmaker, Session
from typing import Optional

from news_aggregator.config import settings
from news_aggregator.models import Base, NewsArticle, Subscriber, ArticleCreate




engine = create_engine(settings.db_url, pool_pre_ping=True)



SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
)



def create_tables() -> None:
    """
    Creates all tables in PostgreSQL if they don't exist.
    Safe to run multiple times — skips existing tables.
    Called once when app starts in main.py
    """
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables ready!")



def get_session() -> Session:
    """Returns a fresh database session."""
    return SessionLocal()



def save_article(article_data: ArticleCreate) -> Optional[NewsArticle]:
    """
    Saves a new article to the database.
    If video_id already exists → skips silently (no duplicates).
    """
    with get_session() as session:

        
        existing = session.execute(
            select(NewsArticle).where(
                NewsArticle.video_id == article_data.video_id
            )
        ).scalar_one_or_none()

        if existing:
            print(f"⏭️  Already exists: {article_data.title[:50]}")
            return None

        
        article = NewsArticle(**article_data.model_dump())
        session.add(article)
        session.commit()
        session.refresh(article)

        print(f"💾 Saved: {article.title[:50]}")
        return article



def update_article_summary(
    video_id: str,
    summary: str,
    category: str,
    tags: list[str]
) -> None:
    """
    After Groq LLM processes a transcript,
    saves the summary and marks article as processed.
    """
    with get_session() as session:
        session.execute(
            update(NewsArticle)
            .where(NewsArticle.video_id == video_id)
            .values(
                summary=summary,
                category=category,
                tags=tags,
                is_processed=True
            )
        )
        session.commit()
        print(f"🤖 Summary saved for: {video_id}")



def get_unprocessed_articles() -> list[NewsArticle]:
    """
    Returns articles that are fetched but NOT yet summarized.
    Used by summarizer.py.
    """
    with get_session() as session:
        results = session.execute(
            select(NewsArticle).where(
                NewsArticle.is_processed == False
            )
        ).scalars().all()
        return list(results)



def get_unemailed_articles() -> list[NewsArticle]:
    """
    Returns summarized articles not yet sent in a digest.
    Used by mailer.py every 24 hours.
    """
    with get_session() as session:
        results = session.execute(
            select(NewsArticle)
            .where(
                NewsArticle.is_processed == True,
                NewsArticle.is_emailed == False
            )
            .order_by(NewsArticle.published_at.desc())
        ).scalars().all()
        return list(results)



def mark_articles_as_emailed(article_ids: list[int]) -> None:
    """
    After sending digest, marks articles so they
    don't appear in the next digest.
    """
    with get_session() as session:
        session.execute(
            update(NewsArticle)
            .where(NewsArticle.id.in_(article_ids))
            .values(is_emailed=True)
        )
        session.commit()
        print(f"📧 Marked {len(article_ids)} articles as emailed.")



def add_subscriber(email: str) -> None:
    """Adds a new subscriber. Skips if already exists."""
    with get_session() as session:
        existing = session.execute(
            select(Subscriber).where(Subscriber.email == email)
        ).scalar_one_or_none()

        if existing:
            print(f"⏭️  Already subscribed: {email}")
            return

        session.add(Subscriber(email=email))
        session.commit()
        print(f"✅ Subscribed: {email}")



def get_active_subscribers() -> list[str]:
    """
    Returns all active subscriber emails.
    Used by mailer.py to know who to send digest to.
    """
    with get_session() as session:
        results = session.execute(
            select(Subscriber.email).where(
                Subscriber.is_active == True
            )
        ).scalars().all()
        return list(results)