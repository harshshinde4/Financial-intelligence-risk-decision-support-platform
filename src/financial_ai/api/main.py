from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from financial_ai.api.routes.agent import router as agent_router
from financial_ai.api.routes.analytics import router as analytics_router
from financial_ai.api.routes.companies import router as companies_router
from financial_ai.api.routes.explainability import router as explainability_router
from financial_ai.api.routes.health import router as health_router
from financial_ai.api.routes.market import router as market_router
from financial_ai.api.routes.ml import router as ml_router
from financial_ai.api.routes.nlp import router as nlp_router
from financial_ai.api.routes.rag import router as rag_router
from financial_ai.config.logging import configure_logging
from financial_ai.config.settings import get_settings
from financial_ai.data.normalization import InvalidSymbolError

settings = get_settings()
configure_logging(settings.log_level)
logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("application_startup", environment=settings.app_env)
    yield
    logger.info("application_shutdown")


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="Financial Intelligence & Risk Decision Support Platform",
    lifespan=lifespan,
)


def _error_response(
    status_code: int,
    code: str,
    message: str,
    *,
    details: list[dict] | None = None,
) -> JSONResponse:
    error = {
        "code": code,
        "message": message,
    }
    if details is not None:
        error["details"] = details

    return JSONResponse(
        status_code=status_code,
        content={"error": error},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    # Deliberately omit submitted input values from public error responses.
    details = [
        {
            "location": list(item.get("loc", ())),
            "message": item.get("msg", "Invalid value."),
            "type": item.get("type", "value_error"),
        }
        for item in exc.errors()
    ]

    logger.info(
        "request_validation_failed",
        path=request.url.path,
        method=request.method,
        error_count=len(details),
    )

    return _error_response(
        422,
        "VALIDATION_ERROR",
        "The request contains invalid fields.",
        details=details,
    )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(
    request: Request,
    exc: StarletteHTTPException,
) -> JSONResponse:
    status_code = exc.status_code

    # Do not return potentially sensitive internal details for server errors.
    if status_code >= 500:
        if status_code == 502:
            code = "UPSTREAM_ERROR"
            message = "An upstream service failed to process the request."
        elif status_code == 503:
            code = "SERVICE_UNAVAILABLE"
            message = "The requested service is temporarily unavailable."
        else:
            code = "INTERNAL_SERVER_ERROR"
            message = "An unexpected server error occurred."
    else:
        code_by_status = {
            400: "BAD_REQUEST",
            401: "UNAUTHORIZED",
            403: "FORBIDDEN",
            404: "NOT_FOUND",
            405: "METHOD_NOT_ALLOWED",
            409: "CONFLICT",
            413: "PAYLOAD_TOO_LARGE",
            422: "REQUEST_REJECTED",
            429: "RATE_LIMITED",
        }
        code = code_by_status.get(status_code, "HTTP_ERROR")

        detail = exc.detail
        message = detail if isinstance(detail, str) else "The request could not be completed."

    logger.info(
        "http_request_error",
        path=request.url.path,
        method=request.method,
        status_code=status_code,
        error_code=code,
    )

    return _error_response(status_code, code, message)


@app.exception_handler(InvalidSymbolError)
async def invalid_symbol_handler(request, exc: InvalidSymbolError):
    from fastapi.responses import JSONResponse

    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "The ticker symbol is invalid.",
                "details": [{"message": str(exc)}],
            }
        },
    )


@app.exception_handler(Exception)
async def unexpected_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    logger.error(
        "unhandled_application_exception",
        path=request.url.path,
        method=request.method,
        exception_type=type(exc).__name__,
        exc_info=(type(exc), exc, exc.__traceback__),
    )

    return _error_response(
        500,
        "INTERNAL_SERVER_ERROR",
        "An unexpected server error occurred.",
    )


app.include_router(health_router, prefix=settings.api_v1_prefix)
app.include_router(companies_router, prefix=settings.api_v1_prefix)
app.include_router(market_router, prefix=settings.api_v1_prefix)
app.include_router(agent_router, prefix=settings.api_v1_prefix)
app.include_router(analytics_router, prefix=settings.api_v1_prefix)
app.include_router(ml_router, prefix=settings.api_v1_prefix)
app.include_router(nlp_router, prefix=settings.api_v1_prefix)
app.include_router(explainability_router, prefix=settings.api_v1_prefix)
app.include_router(rag_router, prefix=settings.api_v1_prefix)
