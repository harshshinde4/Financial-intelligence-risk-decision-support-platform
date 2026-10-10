from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class HealthResponse(BaseModel):
    status: str
    service: str
    environment: str
    timestamp: datetime


class CompanyCreate(BaseModel):
    ticker: str = Field(min_length=1, max_length=32)
    name: str = Field(min_length=1, max_length=255)
    exchange: str | None = None
    sector: str | None = None
    industry: str | None = None


class CompanyResponse(CompanyCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime


class MarketIngestionRequest(BaseModel):
    ticker: str
    start: datetime
    end: datetime


class MarketPriceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    trade_date: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int
