from __future__ import annotations

from fastapi import APIRouter, HTTPException

from financial_ai.nlp.schemas import IntelligenceResponse, NewsArticle
from financial_ai.nlp.service import analyze_articles

router = APIRouter(prefix="/nlp", tags=["Financial NLP & Event Intelligence"])


@router.post("/{ticker}/analyze", response_model=IntelligenceResponse)
def analyze_news(
    ticker: str, articles: list[NewsArticle], use_finbert: bool = True
) -> IntelligenceResponse:
    if not articles:
        raise HTTPException(status_code=422, detail="At least one news article is required")
    return analyze_articles(ticker, articles, use_finbert=use_finbert)
