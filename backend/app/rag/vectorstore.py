"""VectorStore の永続化ロジック。"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from langchain_community.embeddings import FakeEmbeddings
from langchain_community.vectorstores import Chroma, FAISS
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings

from app.config import get_settings


class VectorStoreError(RuntimeError):
    pass


class PersistResult(dict):
    backend: Literal["faiss", "chroma"]
    path: str


def persist_documents(documents: list[Document], persist_dir: Path) -> PersistResult:
    if not documents:
        raise VectorStoreError("documents must not be empty")

    persist_dir.mkdir(parents=True, exist_ok=True)
    embedding = _resolve_embedding()

    faiss_dir = persist_dir / "faiss"
    chroma_dir = persist_dir / "chroma"

    try:
        store = FAISS.from_documents(documents, embedding)
        store.save_local(str(faiss_dir), index_name="wake_faiss")
        return PersistResult(backend="faiss", path=str(faiss_dir))
    except Exception:
        store = Chroma.from_documents(documents, embedding, persist_directory=str(chroma_dir))
        store.persist()
        return PersistResult(backend="chroma", path=str(chroma_dir))


def _resolve_embedding():
    settings = get_settings()
    if settings.mode == "live" and settings.openai_api_key:
        return OpenAIEmbeddings(api_key=settings.openai_api_key, chunk_size=64)
    # FakeEmbeddings は determinisitc でテストや MODE=fake に最適
    return FakeEmbeddings(size=1536)
