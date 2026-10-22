"""Financial Analyst Agent API."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from financial_ai.agent.service import analyze_financial_question
from financial_ai.db.session import get_db

router = APIRouter(prefix="/agent", tags=["Financial Analyst Agent"])


class AnalyzeRequest(BaseModel):
    ticker: str = Field(min_length=1, max_length=30)
    question: str = Field(min_length=3, max_length=2000)


@router.post("/analyze")
def analyze(
    request: AnalyzeRequest,
    db: Session = Depends(get_db),
) -> dict[str, object]:
    return analyze_financial_question(
        question=request.question,
        ticker=request.ticker,
        db=db,
    )
