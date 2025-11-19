from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings, get_runtime_mode, get_llm_provider
from .db import database
from .models import HealthResponse
from .routers import profile, recommend, articles, jobs


def create_app() -> FastAPI:
    settings = get_settings()
    application = FastAPI(title="WAKE Career AI Agent", version="0.1.0")

    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    application.include_router(profile.router)
    application.include_router(recommend.router)
    application.include_router(articles.router)
    application.include_router(jobs.router)

    @application.on_event("startup")
    async def _ensure_defaults() -> None:
        database.ensure_profile()

    @application.get("/", tags=["meta"])
    async def root(request: Request) -> dict[str, str]:
        hostname = str(request.base_url).rstrip("/")
        return {"message": f"hello! please use this hostname: {hostname}"}

    @application.get("/api/health", response_model=HealthResponse)
    async def health_check() -> HealthResponse:
        return HealthResponse(ok=True, mode=get_runtime_mode(), provider="OpenAI")

    return application


app = create_app()
