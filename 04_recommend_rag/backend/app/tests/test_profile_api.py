import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
from app.db import database
from app.main import create_app


@pytest.fixture(autouse=True)
def reset_settings(monkeypatch):
    """各テスト後に Settings キャッシュをクリアする。"""
    yield
    get_settings.cache_clear()
    database.close()


@pytest.fixture
def sqlite_client(tmp_path, monkeypatch) -> TestClient:
    db_file = tmp_path / "app.db"
    monkeypatch.setenv("MODE", "fake")
    monkeypatch.setenv("DB_MODE", "sqlite")
    monkeypatch.setenv("SQLITE_PATH", str(db_file))
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_file}")
    get_settings.cache_clear()
    database.close()
    app = create_app()
    return TestClient(app)


@pytest.fixture
def json_client(tmp_path, monkeypatch) -> TestClient:
    json_dir = tmp_path / "json-db"
    monkeypatch.setenv("MODE", "fake")
    monkeypatch.setenv("DB_MODE", "json")
    monkeypatch.setenv("JSON_DB_DIR", str(json_dir))
    get_settings.cache_clear()
    database.override_storage_dir(json_dir)
    database.close()
    app = create_app()
    return TestClient(app)


def _sample_payload() -> dict:
    return {
        "name": "Alice",
        "years": 5,
        "current_role": "Frontend Engineer",
        "target_role": "AI Product Manager",
        "skills": ["React", "Python"],
        "interests": ["Career Coaching"],
        "notes": "Looking for AI-assisted workflows",
    }


def test_profile_round_trip_sqlite(sqlite_client: TestClient) -> None:
    res = sqlite_client.get("/api/profile")
    assert res.status_code == 200

    payload = _sample_payload()
    res = sqlite_client.put("/api/profile", json=payload)
    assert res.status_code == 200
    body = res.json()
    assert body["name"] == payload["name"]
    assert body["updated_at"]

    res = sqlite_client.get("/api/profile")
    assert res.status_code == 200
    assert res.json()["current_role"] == payload["current_role"]


def test_profile_round_trip_json(json_client: TestClient) -> None:
    res = json_client.get("/api/profile")
    assert res.status_code == 200
    payload = _sample_payload()
    res = json_client.put("/api/profile", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["interests"] == payload["interests"]

    res = json_client.get("/api/profile")
    assert res.status_code == 200
    assert res.json()["name"] == payload["name"]
