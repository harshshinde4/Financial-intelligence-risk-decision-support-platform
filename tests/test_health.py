from fastapi.testclient import TestClient

from financial_ai.api.main import app


def test_health() -> None:
    with TestClient(app) as client:
        response = client.get("/api/v1/health")

    assert response.status_code == 200

    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["service"] == "Financial Intelligence Platform"
