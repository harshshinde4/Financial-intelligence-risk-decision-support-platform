from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class NewsArticle(BaseModel):
    article_id: str
    published_at: datetime
    headline: str
    body: str = ""
    source: str = "unknown"
    url: str | None = None
    ticker: str | None = None


class SentimentResult(BaseModel):
    label: str
    score: float
    positive: float
    negative: float
    neutral: float


class EventResult(BaseModel):
    event_type: str
    severity: str
    confidence: float
    matched_terms: list[str] = Field(default_factory=list)


class ArticleIntelligence(BaseModel):
    article: NewsArticle
    sentiment: SentimentResult
    event: EventResult
    entities: list[str] = Field(default_factory=list)


class IntelligenceResponse(BaseModel):
    ticker: str
    articles: list[ArticleIntelligence]
    aggregate_sentiment: float
    event_counts: dict[str, int]
