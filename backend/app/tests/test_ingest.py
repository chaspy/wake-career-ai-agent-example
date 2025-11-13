from pathlib import Path

from langchain_core.documents import Document

from app.config import get_settings
from app.db import database
from app.models import ArticleMetadata
from app.rag import ingest
from app.rag.vectorstore import persist_documents


def _write_sample(tmp_path: Path) -> Path:
    sample = tmp_path / "sample.md"
    sample.write_text(
        """---
title: Sample Article
source_url: https://wake-career.jp/articles/sample
published: 2024-05-01
tags:
  - sample
---

# heading

body text for WAKE sample article.
""",
        encoding="utf-8",
    )
    return sample


def test_prepare_documents_returns_metadata(tmp_path):
    _write_sample(tmp_path)
    docs, metas = ingest.prepare_documents(tmp_path)
    assert len(docs) >= 1
    assert isinstance(docs[0], Document)
    assert metas[0].slug.startswith("sample")
    assert docs[0].metadata["line"] == 1


def test_vectorstore_persist(tmp_path, monkeypatch):
    monkeypatch.setenv("MODE", "fake")
    get_settings.cache_clear()
    doc = Document(page_content="content chunk", metadata={"slug": "sample", "title": "Sample"})
    result = persist_documents([doc], tmp_path)
    assert result["backend"] in {"faiss", "chroma"}
    assert Path(result["path"]).exists()


def test_article_index_saved_in_json(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_MODE", "json")
    monkeypatch.setenv("JSON_DB_DIR", str(tmp_path))
    get_settings.cache_clear()
    database.override_storage_dir(tmp_path)
    articles = [
        ArticleMetadata(
            slug="sample", title="Sample Article", source_url="https://wake-career.jp", tags=["sample"], published="2024-01-01"
        )
    ]
    saved = database.save_article_index(articles)
    assert saved[0].slug == "sample"
    data_path = tmp_path / "article_index.json"
    assert data_path.exists()
