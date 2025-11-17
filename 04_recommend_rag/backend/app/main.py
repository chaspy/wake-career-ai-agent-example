from fastapi import FastAPI
from pydantic import BaseModel
from pathlib import Path
import json

DATA_DIR = Path(__file__).resolve().parent / "data"
ARTICLES_DIR = DATA_DIR / "articles"
ARTICLES_DIR.mkdir(parents=True, exist_ok=True)

class Health(BaseModel):
    ok: bool
    phase: str

class ArticleSummary(BaseModel):
    slug: str
    title: str
    source_url: str

class ArticleDetail(ArticleSummary):
    body: str

class Recommendation(BaseModel):
    id: str
    title: str
    url: str
    score: float
    excerpt: str
    reasons: list[str]
    citations: list[str]

class RecommendationResponse(BaseModel):
    recommendations: list[Recommendation]
    mode: str = "fake"

app = FastAPI(title="04_recommend_rag")

@app.get("/api/health", response_model=Health)
def health():
    return Health(ok=True, phase="04_recommend_rag")

@app.get("/api/articles", response_model=list[ArticleSummary])
def list_articles():
    return [_load_article(path, body=False) for path in ARTICLES_DIR.glob("*.md")]

@app.get("/api/articles/{slug}", response_model=ArticleDetail)
def get_article(slug: str):
    path = ARTICLES_DIR / f"{slug}.md"
    if not path.exists():
        raise RuntimeError("article not found")
    return _load_article(path, body=True)

@app.post("/api/recommendations", response_model=RecommendationResponse)
def recommend():
    # 最小の fake RAG: 先頭の記事をそのまま推薦し、疑似スコアと理由を返す。
    articles = list(ARTICLES_DIR.glob("*.md"))
    if not articles:
        return RecommendationResponse(recommendations=[], mode="fake")
    art = _load_article(articles[0], body=True)
    rec = Recommendation(
        id=art.slug,
        title=art.title,
        url=art.source_url,
        score=0.9,
        excerpt=art.body[:180],
        reasons=["プロフィール未使用のサンプル推薦です", "本文の冒頭を抜粋してプレビューします", "RAG本実装前のダミー応答です"],
        citations=[art.source_url],
    )
    return RecommendationResponse(recommendations=[rec], mode="fake")


def _load_article(path: Path, body: bool):
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    title = lines[0].lstrip('# ').strip() if lines else path.stem
    source = ""
    for line in lines[:5]:
        if line.startswith("source_url:"):
            source = line.split(":", 1)[1].strip()
    data = {
        "slug": path.stem,
        "title": title,
        "source_url": source or "https://example.com",
    }
    if body:
        data["body"] = text
    return ArticleDetail(**data) if body else ArticleSummary(**data)

