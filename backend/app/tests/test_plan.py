from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import create_app


def test_plan_endpoint_returns_report(monkeypatch):
    monkeypatch.setenv("MODE", "fake")
    get_settings.cache_clear()

    app = create_app()
    client = TestClient(app)

    payload = {
        "profile": {
            "name": "Planner Tester",
            "years": 5,
            "current_role": "Backend Engineer",
            "target_role": "AI Product Manager",
            "skills": ["Python", "RAG"],
            "interests": ["Career"],
        },
        "recommendations": [
            {
                "id": "rec-1",
                "title": "WAKE Article",
                "url": "https://wake-career.jp/media/sample",
                "score": 0.95,
                "excerpt": "サンプル記事です",
                "reasons": ["Example reason"],
                "citations": [
                    {"source_url": "https://wake-career.jp/media/sample", "title": "WAKE Article"}
                ],
            }
        ],
        "jobs": [
            {
                "id": "job-1",
                "title": "AI PM",
                "company": "WAKE",
                "url": "https://example.com/jobs/1",
                "source": "sample-feed",
            }
        ],
    }

    response = client.post("/api/plan", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["mode"] == "fake"
    assert len(data["profileInsights"]) >= 1
    assert len(data["careerOptions"]) >= 1
    assert data["careerOptions"][0]["title"]
