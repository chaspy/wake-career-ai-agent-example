from functools import lru_cache

from fastapi import APIRouter, HTTPException, status

from app.config import get_runtime_mode
from app.db import database
from app.models import PlanReport, PlanRequest, PlanResponse
from app.planner.graph import build_planner_graph

router = APIRouter(prefix="/api/plan", tags=["plan"])


@lru_cache(maxsize=1)
def get_graph():
    return build_planner_graph()


@router.post("", response_model=PlanResponse)
async def generate_plan(payload: PlanRequest) -> PlanResponse:
    profile = payload.profile or database.get_profile()
    if not payload.recommendations:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="recommendations are required",
        )
    state = {
        "profile": profile.model_dump() if profile else None,
        "recommendations": [rec.model_dump() for rec in payload.recommendations],
        "jobs": [job.model_dump() for job in payload.jobs],
    }

    try:
        result = get_graph().invoke(state)
    except Exception as exc:  # pragma: no cover
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc

    plan_dict = result.get("plan")
    if not plan_dict:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="plan generation failed",
        )

    report = PlanReport(**plan_dict)
    logs = [str(item) for item in result.get("logs", [])]
    return PlanResponse(
        **report.model_dump(),
        mode=get_runtime_mode(),
        logs=logs,
    )
