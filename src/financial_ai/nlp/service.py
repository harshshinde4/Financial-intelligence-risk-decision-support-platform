from __future__ import annotations

from collections import Counter

from financial_ai.nlp.entities import extract_ticker_entities
from financial_ai.nlp.events import classify_event
from financial_ai.nlp.schemas import ArticleIntelligence, IntelligenceResponse, NewsArticle
from financial_ai.nlp.sentiment import analyze_sentiment


def analyze_article(article: NewsArticle, use_finbert: bool = True) -> ArticleIntelligence:
    text = f"{article.headline}\n{article.body}".strip()
    return ArticleIntelligence(
        article=article,
        sentiment=analyze_sentiment(text, use_finbert=use_finbert),
        event=classify_event(text),
        entities=extract_ticker_entities(text),
    )


def analyze_articles(
    ticker: str, articles: list[NewsArticle], use_finbert: bool = True
) -> IntelligenceResponse:
    normalized = ticker.upper()
    results = [analyze_article(article, use_finbert=use_finbert) for article in articles]
    results = [r for r in results if normalized in r.entities or r.article.ticker == normalized]
    sentiment_values = [r.sentiment.positive - r.sentiment.negative for r in results]
    aggregate = sum(sentiment_values) / len(sentiment_values) if sentiment_values else 0.0
    counts = Counter(r.event.event_type for r in results)
    return IntelligenceResponse(
        ticker=normalized,
        articles=results,
        aggregate_sentiment=float(aggregate),
        event_counts=dict(counts),
    )
