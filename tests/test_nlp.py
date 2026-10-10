from datetime import UTC, datetime

from financial_ai.nlp.events import classify_event
from financial_ai.nlp.schemas import NewsArticle
from financial_ai.nlp.sentiment import analyze_sentiment
from financial_ai.nlp.service import analyze_article, analyze_articles


def article() -> NewsArticle:
    return NewsArticle(
        article_id="test-1",
        published_at=datetime(2026, 9, 28, tzinfo=UTC),
        headline="AAPL reports record revenue and strong profit growth",
        body="Apple beat expectations and raised guidance.",
        source="test",
        ticker="AAPL",
    )


def test_event_classification():
    result = classify_event("Company announces earnings and revenue guidance")
    assert result.event_type == "earnings"
    assert result.severity == "medium"


def test_fallback_sentiment():
    result = analyze_sentiment("record growth and strong profit", use_finbert=False)
    assert result.label == "positive"
    assert result.positive > result.negative


def test_article_analysis():
    result = analyze_article(article(), use_finbert=False)
    assert result.article.ticker == "AAPL"
    assert "AAPL" in result.entities
    assert result.sentiment.label == "positive"


def test_aggregate_analysis():
    result = analyze_articles("AAPL", [article()], use_finbert=False)
    assert result.ticker == "AAPL"
    assert len(result.articles) == 1
    assert result.aggregate_sentiment > 0
    assert result.event_counts["earnings"] == 1
