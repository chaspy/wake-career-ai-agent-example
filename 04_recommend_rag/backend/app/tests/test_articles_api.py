from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
from app.db import database
from app.main import create_app
from app.models import ArticleMetadata


@pytest.fixture(autouse=True)
def reset_settings():
    yield
    get_settings.cache_clear()
    database.close()


def _seed_article(tmp_db: Path, tmp_articles: Path) -> str:
    slug = "sample-article"
    markdown = tmp_articles / f"{slug}.md"
    markdown.write_text(
        """---
title: Sample Article
source_url: https://wake-career.jp/media/sample
published: 2025-07-01
tags:
  - coaching
---

# Heading

WAKE Career 実データ本文。
""",
        encoding="utf-8",
    )
    database.override_storage_dir(tmp_db)
    database.save_article_index(
        [
            ArticleMetadata(
                slug=slug,
                title="Sample Article",
                source_url="https://wake-career.jp/media/sample",
                tags=["coaching"],
                category="career",
                published="2025-07-01",
            )
        ]
    )
    return slug


def test_articles_list_and_detail(tmp_path, monkeypatch):
    tmp_db = tmp_path / "db"
    tmp_articles = tmp_path / "articles"
    tmp_articles.mkdir()

    monkeypatch.setenv("DB_MODE", "json")
    monkeypatch.setenv("JSON_DB_DIR", str(tmp_db))
    monkeypatch.setenv("ARTICLES_DIR", str(tmp_articles))
    get_settings.cache_clear()
    slug = _seed_article(tmp_db, tmp_articles)

    app = create_app()
    client = TestClient(app)

    res = client.get("/api/articles")
    assert res.status_code == 200
    data = res.json()
    assert data[0]["slug"] == slug
    assert data[0]["tags"] == ["coaching"]

    res = client.get(f"/api/articles/{slug}")
    assert res.status_code == 200
    detail = res.json()
    assert "WAKE Career" in detail["body"]
    assert detail["category"] == "career"
