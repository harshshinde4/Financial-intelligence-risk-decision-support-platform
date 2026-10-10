from datetime import UTC, datetime

from fastapi import APIRouter

from financial_ai.api.schemas import HealthResponse
from financial_ai.config.settings import get_settings

router = APIRouter(tags=["system"])


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    settings = get_settings()

    return HealthResponse(
        status="ok",
        service=settings.app_name,
        environment=settings.app_env,
        timestamp=datetime.now(UTC),
    )
