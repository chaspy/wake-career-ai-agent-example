from fastapi import APIRouter

from app.jobs import search_jobs
from app.models import JobSearchRequest, JobSearchResponse

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


@router.post("/search", response_model=JobSearchResponse)
async def search_job_endpoint(payload: JobSearchRequest) -> JobSearchResponse:
    jobs = search_jobs(payload.query, payload.location, payload.limit)
    sources = sorted({job.source for job in jobs})
    return JobSearchResponse(jobs=jobs, sources=sources)
