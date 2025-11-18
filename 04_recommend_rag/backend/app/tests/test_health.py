from fastapi.testclient import TestClient

from app.main import app


def test_health_endpoint_returns_mode() -> None:
    client = TestClient(app)
    response = client.get("/api/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert payload["mode"] in {"fake", "live"}
