from fastapi.testclient import TestClient
from langchain_core.documents import Document

from app.config import get_settings
from app.main import create_app
from app.rag import retriever
from app.routers import recommend


class DummyRetriever:
    def __init__(self, docs):
        self.docs = docs

    def invoke(self, query):
        return self.docs


def test_recommendations_return_citations(monkeypatch):
    monkeypatch.setenv("MODE", "fake")
    get_settings.cache_clear()

    doc = Document(
        page_content="AI プロダクトPMが1on1で学んだ知見をまとめた記事です。",
        metadata={
            "slug": "ai-pm",
            "title": "WAKE Career 実践AI PM",
            "source_url": "https://wake-career.jp/media/wakeskill-1on1",
            "line": 5,
            "tags": ["AI", "1on1"],
        },
    )

    monkeypatch.setattr(retriever, "get_retriever", lambda k=3: DummyRetriever([doc]))
    recommend.get_graph.cache_clear()

    app = create_app()
    client = TestClient(app)

    payload = {"query": "AI PM", "top_k": 1}
    response = client.post("/api/recommendations", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["mode"] == "fake"
    assert len(data["recommendations"]) == 1
    citation = data["recommendations"][0]["citations"][0]
    assert citation["source_url"].startswith("https://wake-career.jp/")
    assert data["recommendations"][0]["reasons"]
