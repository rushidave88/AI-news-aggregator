

from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, Boolean, Integer, DateTime, ARRAY
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from pydantic import BaseModel


# ─── SQLALCHEMY BASE ─────────────────────────────────────────────────
class Base(DeclarativeBase):
    pass


# ─── DATABASE TABLE: news_articles ───────────────────────────────────
class NewsArticle(Base):
    __tablename__ = "news_articles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    video_id: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)

    title: Mapped[str] = mapped_column(Text, nullable=False)

    channel_name: Mapped[str] = mapped_column(String(100), nullable=False)

    channel_id: Mapped[str] = mapped_column(String(50), nullable=False)

    published_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    fetched_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    transcript: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    category: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    tags: Mapped[Optional[list]] = mapped_column(ARRAY(String), nullable=True)

    video_url: Mapped[str] = mapped_column(Text, nullable=False)

    thumbnail_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    is_processed: Mapped[bool] = mapped_column(Boolean, default=False)

    is_emailed: Mapped[bool] = mapped_column(Boolean, default=False)

    def __repr__(self) -> str:
        return f"<NewsArticle id={self.id} title='{self.title[:40]}'>"


# ─── DATABASE TABLE: subscribers ─────────────────────────────────────
class Subscriber(Base):
    __tablename__ = "subscribers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    subscribed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<Subscriber email='{self.email}'>"


# ─── PYDANTIC MODEL: validate before saving ───────────────────────────
class ArticleCreate(BaseModel):
    video_id: str
    title: str
    channel_name: str
    channel_id: str
    published_at: datetime
    video_url: str
    thumbnail_url: Optional[str] = None
    transcript: Optional[str] = None
    summary: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[list[str]] = []
    is_processed: bool = False
    is_emailed: bool = False



class ArticleSummary(BaseModel):
    summary: str
    category: str
    tags: list[str]