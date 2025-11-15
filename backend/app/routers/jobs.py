from fastapi import APIRouter

from app.db import database
from app.jobs import search_jobs
from app.models import JobSearchRequest, JobSearchResponse

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


@router.post("/search", response_model=JobSearchResponse)
async def search_job_endpoint(payload: JobSearchRequest) -> JobSearchResponse:
    profile = payload.profile or database.get_profile()
    result = search_jobs(profile, payload.query, payload.location, payload.limit)
    return JobSearchResponse(jobs=result.jobs, sources=result.sources, queries=result.queries)
