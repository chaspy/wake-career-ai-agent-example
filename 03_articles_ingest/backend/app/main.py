from fastapi import FastAPI, HTTPException
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

class Profile(BaseModel):
    name: str
    years: int
    current_role: str
    target_role: str
    skills: list[str] = []
    interests: list[str] = []
    notes: str | None = None

app = FastAPI(title="03_articles_ingest")

@app.get("/api/health", response_model=Health)
def health():
    return Health(ok=True, phase="03_articles_ingest")

@app.get("/api/articles", response_model=list[ArticleSummary])
def list_articles():
    items = []
    for path in ARTICLES_DIR.glob("*.md"):
        items.append(_load_article(path, body=False))
    return items

@app.get("/api/articles/{slug}", response_model=ArticleDetail)
def get_article(slug: str):
    path = ARTICLES_DIR / f"{slug}.md"
    if not path.exists():
        raise HTTPException(status_code=404, detail="article not found")
    return _load_article(path, body=True)

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

