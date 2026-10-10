from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.testclient import TestClient
from pydantic import BaseModel, Field

from financial_ai.api.main import app


class ValidationPayload(BaseModel):
    top_k: int = Field(ge=1, le=10)


def test_unknown_route_uses_standard_error_format():
    client = TestClient(app)

    response = client.get("/api/v1/route-that-does-not-exist")

    assert response.status_code == 404
    body = response.json()
    assert body["error"]["code"] == "NOT_FOUND"
    assert "message" in body["error"]


def test_invalid_request_uses_validation_error_format():
    test_app = FastAPI()
    from financial_ai.api.main import validation_exception_handler

    test_app.add_exception_handler(
        RequestValidationError,
        validation_exception_handler,
    )

    @test_app.post("/validate")
    def validate(payload: ValidationPayload):
        return payload

    client = TestClient(test_app)
    response = client.post("/validate", json={"top_k": 0})

    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] == "VALIDATION_ERROR"
    assert body["error"]["details"][0]["location"] == ["body", "top_k"]


def test_health_endpoint_still_works():
    client = TestClient(app)

    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
