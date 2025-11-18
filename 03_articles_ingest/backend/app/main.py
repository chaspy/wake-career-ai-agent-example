from __future__ import annotations

import json
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
VSTORE_DIR.mkdir(parents=True, exist_ok=True)
ARTICLES_DIR.mkdir(parents=True, exist_ok=True)
PROFILE_FILE = DATA_DIR / "profile.json"


class Health(BaseModel):
    ok: bool
    phase: str
    mode: str
    provider: str


class Profile(BaseModel):
    name: str
    years: int
    current_role: str
    target_role: str
    skills: List[str] = Field(default_factory=list)
    interests: List[str] = Field(default_factory=list)
    notes: str | None = None


class ProfileResponse(Profile):
    pass


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


class AdviceRequest(BaseModel):
    question: str = Field("次にどんな行動を取れば良いですか？", min_length=1)


class AdviceResponse(BaseModel):
    provider: str
    answer: str


app = FastAPI(title="03_articles_rag", version="0.3.0")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def runtime_mode() -> str:
    return "live" if os.getenv("OPENAI_API_KEY") else "fake"


def provider_name() -> str:
    return "OpenAI" if os.getenv("OPENAI_API_KEY") else "fake"


@lru_cache(maxsize=1)
def get_vectorstore() -> FAISS:
    index_file = VSTORE_DIR / "faiss.index"
    if not index_file.exists():
        raise FileNotFoundError("vectorstore not seeded; run `uv run python scripts/seed.py`")
    return FAISS.load_local(str(VSTORE_DIR), _embedding_fn(), allow_dangerous_deserialization=True)


def _embedding_fn():
    if os.getenv("OPENAI_API_KEY"):
        return OpenAIEmbeddings(model="text-embedding-3-small")
    return FakeEmbeddings(size=1536)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@app.get("/api/health", response_model=Health)
def health() -> Health:
    return Health(ok=True, phase="03_articles_rag", mode=runtime_mode(), provider=provider_name())


@app.get("/api/profile", response_model=ProfileResponse)
def get_profile():
    if not PROFILE_FILE.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="profile not set")
    return _load_profile_or_404()


@app.put("/api/profile", response_model=ProfileResponse)
def upsert_profile(payload: Profile):
    PROFILE_FILE.write_text(payload.model_dump_json(indent=2, ensure_ascii=False), encoding="utf-8")
    return ProfileResponse(**payload.model_dump())


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


@app.post("/api/profile/advice", response_model=AdviceResponse)
def get_profile_advice(payload: AdviceRequest) -> AdviceResponse:
    profile = _load_profile_or_404()
    messages = _build_prompt(profile, payload.question)
    if os.getenv("OPENAI_API_KEY"):
        answer = _call_llm(messages)
        provider = "openai"
    else:
        answer = _fake_answer(profile, payload.question)
        provider = "fake"
    return AdviceResponse(provider=provider, answer=answer)


# ---------------------------------------------------------------------------
# Internal
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
        return [f"fake: '{query}' と関連しそうな本文を抽出しました"]
    llm = ChatOpenAI(model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"), temperature=0)
    prompt = (
        "ユーザの関心と本文を渡すので、1文で推薦理由を出してください。"
        "必ず日本語で簡潔に。\n"
        f"[query]\n{query}\n[context]\n{text[:500]}"
    )
    out = llm.invoke([{"role": "user", "content": prompt}])
    return [out.content]


def _load_profile_or_404() -> ProfileResponse:
    if not PROFILE_FILE.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="profile not set")
    data = json.loads(PROFILE_FILE.read_text(encoding="utf-8"))
    return ProfileResponse(**data)


def _build_prompt(profile: ProfileResponse, question: str) -> List[dict[str, str]]:
    profile_summary = (
        f"氏名: {profile.name}\n"
        f"経験年数: {profile.years}年\n"
        f"現在の役割: {profile.current_role}\n"
        f"目標の役割: {profile.target_role}\n"
        f"スキル: {', '.join(profile.skills) if profile.skills else 'なし'}\n"
        f"興味: {', '.join(profile.interests) if profile.interests else 'なし'}\n"
        f"ノート: {profile.notes or 'なし'}"
    )
    system = (
        "あなたは日本語で回答するキャリアコーチです。"
        "与えられたプロフィールを踏まえて、実行可能な次の一手を3つ以内で提案してください。"
        "箇条書きで、最長でも400文字以内にまとめてください。"
    )
    user_prompt = f"プロフィール:\n{profile_summary}\n\n相談内容: {question}"
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user_prompt},
    ]


def _fake_answer(profile: ProfileResponse, question: str) -> str:
    keywords = [*(profile.skills or []), *(profile.interests or [])]
    base = (
        f"{profile.name}さん向けのラフな提案です。\n"
        f"- 目標ロール『{profile.target_role}』に近い案件/記事を週1で調べる\n"
        f"- {profile.current_role}の経験を活かしつつ、{', '.join(keywords[:2]) or '関連分野'}を深堀りする\n"
        f"- 次の行動: {question}"
    )
    return base


def _call_llm(messages: List[dict[str, str]]) -> str:
    llm = ChatOpenAI(model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"), temperature=0.4)
    out = llm.invoke(messages)
    return out.content or ""


# ---------------------------------------------------------------------------
# Utilities (used by seed.py as well)
# ---------------------------------------------------------------------------

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
    # Build vector store
    from langchain_core.documents import Document

    vs = FAISS.from_documents([Document(**d) for d in docs], _embedding_fn())
    vs.save_local(str(vector_dir))


if __name__ == "__main__":
    ingest_articles()
    print(f"ingested {len(list(VSTORE_DIR.glob('*')))} files into {VSTORE_DIR}")
