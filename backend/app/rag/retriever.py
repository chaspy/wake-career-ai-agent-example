"""ベクトルストアから LangChain Retriever を生成する。"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from langchain_community.embeddings import FakeEmbeddings
from langchain_community.vectorstores import Chroma, FAISS
from langchain_openai import OpenAIEmbeddings

from app.config import get_settings

FAISS_INDEX_NAME = "wake_faiss"


class RetrieverNotReadyError(RuntimeError):
    pass


def get_retriever(k: int = 4):
    store = _load_vectorstore()
    return store.as_retriever(search_kwargs={"k": k})


def _load_vectorstore():
    settings = get_settings()
    base_dir = settings.vectorstore_dir
    embedding = _resolve_embedding()

    faiss_dir = base_dir / "faiss"
    if faiss_dir.exists():
        try:
            return FAISS.load_local(
                str(faiss_dir), embedding, index_name=FAISS_INDEX_NAME, allow_dangerous_deserialization=True
            )
        except Exception as exc:  # pragma: no cover - fallback to Chroma below
            print(f"[retriever] failed to load FAISS: {exc}")

    chroma_dir = base_dir / "chroma"
    if chroma_dir.exists():
        return Chroma(persist_directory=str(chroma_dir), embedding_function=embedding)

    raise RetrieverNotReadyError(
        f"Vectorstore not found under {base_dir}. Run `make seed` to ingest WAKE articles before recommending."
    )


def _resolve_embedding():
    settings = get_settings()
    if settings.mode == "live" and settings.openai_api_key:
        return OpenAIEmbeddings(api_key=settings.openai_api_key)
    return FakeEmbeddings(size=1536)
