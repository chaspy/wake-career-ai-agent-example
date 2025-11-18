from functools import lru_cache

from fastapi import APIRouter, HTTPException, status

from app.config import get_runtime_mode, get_settings
from app.db import database
from app.models import RecommendationRequest, RecommendationResponse, Recommendation
from app.rag.graph import build_recommendation_graph
from app.rag.retriever import RetrieverNotReadyError

router = APIRouter(prefix="/api/recommendations", tags=["recommend"])


@lru_cache(maxsize=1)
def get_graph():
    return build_recommendation_graph()


@router.post("", response_model=RecommendationResponse)
async def recommend(payload: RecommendationRequest) -> RecommendationResponse:
    settings = get_settings()
    profile = payload.profile
    if profile is None:
        stored = database.get_profile()
        profile = stored
    state = {
        "profile": profile,
        "query": payload.query,
        "k": payload.top_k,
    }
    try:
        result = get_graph().invoke(state)
    except RetrieverNotReadyError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc

    recs = [
        Recommendation(
            id=rec.get("slug", f"rec-{idx}"),
            title=rec.get("title", "WAKE Article"),
            url=rec.get("url", ""),
            score=rec.get("score", 0.0),
            excerpt=rec.get("excerpt", ""),
            reasons=rec.get("reasons", []),
            citations=rec.get("citations", []),
        )
        for idx, rec in enumerate(result.get("recs", []))
    ]
    return RecommendationResponse(recommendations=recs, mode=get_runtime_mode())
