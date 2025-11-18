from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import List

import frontmatter
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.embeddings import FakeEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter

DATA_DIR = Path(__file__).resolve().parent / "data"
ARTICLES_DIR = DATA_DIR / "articles"
VSTORE_DIR = DATA_DIR / "vectorstore"
ARTICLES_DIR.mkdir(parents=True, exist_ok=True)
VSTORE_DIR.mkdir(parents=True, exist_ok=True)


class Health(BaseModel):
    ok: bool
    phase: str
    mode: str
    provider: str


class ArticleSummary(BaseModel):
    slug: str
    title: str
    source_url: str


class ArticleDetail(ArticleSummary):
    body: str


class Recommendation(BaseModel):
    slug: str
    title: str
    url: str
    score: float = 0.0
    excerpt: str = ""
    reasons: List[str] = Field(default_factory=list)
    citations: List[str] = Field(default_factory=list)


class RecommendationRequest(BaseModel):
    query: str = Field(..., min_length=1)
    top_k: int = Field(3, ge=1, le=10)


class RecommendationResponse(BaseModel):
    recommendations: List[Recommendation]
    mode: str = "fake"


class JobSummary(BaseModel):
    id: str
    title: str
    company: str
    location: str
    url: str
    snippet: str = ""
    published_at: str | None = None


class JobSearchRequest(BaseModel):
    query: str | None = None
    location: str | None = None
    limit: int = Field(5, ge=1, le=20)


class JobSearchResponse(BaseModel):
    jobs: List[JobSummary]
    sources: List[str]
    queries: List[str]


app = FastAPI(title="04_jobs", version="0.4.0")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def runtime_mode() -> str:
    return "live" if os.getenv("OPENAI_API_KEY") else "fake"


def provider_name() -> str:
    return "OpenAI" if os.getenv("OPENAI_API_KEY") else "fake"


def _embedding_fn():
    if os.getenv("OPENAI_API_KEY"):
        return OpenAIEmbeddings(model="text-embedding-3-small")
    return FakeEmbeddings(size=1536)


@lru_cache(maxsize=1)
def get_vectorstore() -> FAISS:
    index_file = VSTORE_DIR / "faiss.index"
    if not index_file.exists():
        raise FileNotFoundError("vectorstore not seeded; run `uv run python scripts/seed.py`")
    return FAISS.load_local(str(VSTORE_DIR), _embedding_fn(), allow_dangerous_deserialization=True)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@app.get("/api/health", response_model=Health)
def health() -> Health:
    return Health(ok=True, phase="04_jobs", mode=runtime_mode(), provider=provider_name())


@app.get("/api/articles", response_model=List[ArticleSummary])
def list_articles():
    return [_load_article(path, body=False) for path in sorted(ARTICLES_DIR.glob("*.md"))]


@app.get("/api/articles/{slug}", response_model=ArticleDetail)
def get_article(slug: str):
    path = ARTICLES_DIR / f"{slug}.md"
    if not path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="article not found")
    return _load_article(path, body=True)


@app.post("/api/recommendations", response_model=RecommendationResponse)
def recommend(payload: RecommendationRequest) -> RecommendationResponse:
    try:
        store = get_vectorstore()
    except FileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc))

    docs = store.similarity_search_with_score(payload.query, k=payload.top_k)
    recs: List[Recommendation] = []
    for doc, score in docs:
        meta = doc.metadata or {}
        recs.append(
            Recommendation(
                slug=meta.get("slug", ""),
                title=meta.get("title", "Untitled"),
                url=meta.get("source_url", ""),
                score=float(score),
                excerpt=doc.page_content[:240],
                reasons=_make_reasons(doc.page_content, payload.query),
                citations=[meta.get("source_url", "")],
            )
        )
    return RecommendationResponse(recommendations=recs, mode=runtime_mode())


@app.post("/api/jobs/search", response_model=JobSearchResponse)
def search_jobs(payload: JobSearchRequest) -> JobSearchResponse:
    q = (payload.query or "エンジニア").strip()
    loc = (payload.location or "Tokyo").strip()
    jobs = _fake_jobs(q, loc)
    limited = jobs[: payload.limit]
    queries = [q]
    sources = sorted({job.url for job in limited})
    return JobSearchResponse(jobs=limited, sources=sources, queries=queries)


# ---------------------------------------------------------------------------
# Internal utils
# ---------------------------------------------------------------------------

def _load_article(path: Path, body: bool):
    post = frontmatter.loads(path.read_text(encoding="utf-8"))
    title = post.get("title") or path.stem.replace("-", " ")
    source = post.get("source_url") or ""
    slug = path.stem
    data = {
        "slug": slug,
        "title": title,
        "source_url": source or "https://example.com",
    }
    if body:
        data["body"] = post.content.strip()
    return ArticleDetail(**data) if body else ArticleSummary(**data)


def _make_reasons(text: str, query: str) -> List[str]:
    if not os.getenv("OPENAI_API_KEY"):
        return [f"fake: '{query}' に関連しそうな本文から抽出"]
    llm = ChatOpenAI(model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"), temperature=0)
    prompt = (
        "ユーザの関心と本文を渡すので、1文で推薦理由を出してください。"
        "必ず日本語で簡潔に。\n"
        f"[query]\n{query}\n[context]\n{text[:500]}"
    )
    out = llm.invoke([{"role": "user", "content": prompt}])
    return [out.content]


def ingest_articles(articles_dir: Path = ARTICLES_DIR, vector_dir: Path = VSTORE_DIR):
    files = sorted(articles_dir.glob("*.md"))
    if not files:
        raise RuntimeError("no markdown files found to ingest")
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=80)
    docs = []
    for path in files:
        post = frontmatter.loads(path.read_text(encoding="utf-8"))
        title = post.get("title") or path.stem
        source = post.get("source_url") or "https://example.com"
        slug = path.stem
        for chunk in splitter.split_text(post.content):
            docs.append(
                {
                    "page_content": chunk,
                    "metadata": {"title": title, "source_url": source, "slug": slug},
                }
            )
    from langchain.schema import Document

    vs = FAISS.from_documents([Document(**d) for d in docs], _embedding_fn())
    vs.save_local(str(vector_dir))


def _fake_jobs(query: str, location: str) -> List[JobSummary]:
    base = [
        JobSummary(
            id="job-1",
            title="AI プロダクトマネージャー",
            company="WAKE Technologies",
            location=location,
            url="https://example.com/jobs/ai-pm",
            snippet=f"{query} に関連する戦略策定とPoC推進を担うポジション。",
        ),
        JobSummary(
            id="job-2",
            title="LLM アプリケーションエンジニア",
            company="NextGen AI",
            location=location,
            url="https://example.com/jobs/llm-eng",
            snippet="LangChain/FAISS を使った検索・生成ワークフローの実装。",
        ),
        JobSummary(
            id="job-3",
            title="データサイエンティスト",
            company="DataCraft",
            location=location,
            url="https://example.com/jobs/ds",
            snippet="ビジネス課題に対して機械学習モデルを設計・運用。",
        ),
    ]
    return base


if __name__ == "__main__":
    ingest_articles()
    print(f"ingested into {VSTORE_DIR}")
