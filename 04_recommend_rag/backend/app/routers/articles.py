from fastapi import APIRouter, HTTPException, status

from app.db import ArticleNotFoundError, database
from app.models import ArticleDetail, ArticleSummary

router = APIRouter(prefix="/api/articles", tags=["articles"])


@router.get("", response_model=list[ArticleSummary])
async def list_articles() -> list[ArticleSummary]:
    articles = database.list_articles()
    return [ArticleSummary(**item.model_dump()) for item in articles]


@router.get("/{slug}", response_model=ArticleDetail)
async def get_article(slug: str) -> ArticleDetail:
    try:
        article = database.get_article(slug)
    except ArticleNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return article
