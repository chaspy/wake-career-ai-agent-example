"""Markdown 記事の取り込み・分割ロジック。"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Tuple

import frontmatter
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

from app.models import ArticleMetadata


@dataclass
class ArticleSnapshot:
    slug: str
    title: str
    source_url: str
    published: str | None
    tags: list[str]
    category: str | None
    body: str


def load_snapshots(articles_dir: Path) -> list[ArticleSnapshot]:
    articles: list[ArticleSnapshot] = []
    if not articles_dir.exists():
        return articles
    for path in sorted(articles_dir.glob("*.md")):
        post = frontmatter.load(path)
        meta = post.metadata or {}
        title = meta.get("title") or path.stem.replace("-", " ")
        source_url = meta.get("source_url", "").strip()
        if not source_url:
            continue
        published_raw = meta.get("published")
        if isinstance(published_raw, (int, float)):
            published = str(published_raw)
        elif hasattr(published_raw, "isoformat"):
            published = published_raw.isoformat()
        else:
            published = published_raw
        tags = _normalize_list(meta.get("tags", []))
        category = meta.get("category")
        slug = meta.get("slug") or path.stem
        body = post.content.strip()
        if not body:
            continue
        articles.append(
            ArticleSnapshot(
                slug=slug,
                title=title,
                source_url=source_url,
                published=published,
                tags=tags,
                category=category,
                body=body,
            )
        )
    return articles


def build_documents(articles: Iterable[ArticleSnapshot]) -> Tuple[list[Document], list[ArticleMetadata]]:
    splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=120)
    documents: list[Document] = []
    metadata_records: list[ArticleMetadata] = []
    for article in articles:
        metadata_records.append(
            ArticleMetadata(
                slug=article.slug,
                title=article.title,
                source_url=article.source_url,
                tags=article.tags,
                category=article.category,
                published=article.published,
            )
        )
        chunks = splitter.split_text(article.body)
        pointer = 0
        for chunk in chunks:
            start_index = article.body.find(chunk, pointer)
            if start_index == -1:
                start_index = article.body.find(chunk)
            pointer = start_index + len(chunk)
            line_number = article.body[:start_index].count("\n") + 1 if start_index >= 0 else 1
            documents.append(
                Document(
                    page_content=chunk,
                    metadata={
                        "slug": article.slug,
                        "title": article.title,
                        "source_url": article.source_url,
                        "tags": article.tags,
                        "category": article.category,
                        "line": line_number,
                    },
                )
            )
    return documents, metadata_records


def prepare_documents(articles_dir: Path) -> Tuple[list[Document], list[ArticleMetadata]]:
    articles = load_snapshots(articles_dir)
    return build_documents(articles)


def _normalize_list(value) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    return []
