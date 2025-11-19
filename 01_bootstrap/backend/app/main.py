from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langchain_openai import ChatOpenAI
import os
import logging
from pathlib import Path

logger = logging.getLogger("bootstrap")
if not logger.handlers:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
logger.setLevel(logging.INFO)

BACKEND_DIR = Path(__file__).resolve().parents[1]
STEP_DIR = BACKEND_DIR.parent
REPO_ROOT = STEP_DIR.parent
ENV_FILES = [BACKEND_DIR / ".env", STEP_DIR / ".env", REPO_ROOT / ".env"]


def _load_env():
    for env_file in ENV_FILES:
        if not env_file.exists():
            continue
        logger.info("loading env vars from %s", env_file)
        for raw in env_file.read_text().splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            if key.strip() not in os.environ:
                os.environ[key.strip()] = value.strip()


_load_env()

app = FastAPI(title="Bootstrap API")
allowed_origins = os.getenv("ALLOWED_ORIGINS")
origins = [o.strip() for o in allowed_origins.split(",")] if allowed_origins else ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class PingRequest(BaseModel):
    prompt: str = "はじめまして！"

class PingResponse(BaseModel):
    reply: str
    mode: str

@app.get("/")
async def root(request: Request) -> dict[str, str]:
    forwarded = request.headers.get("x-forwarded-host")
    if forwarded:
        scheme = request.headers.get("x-forwarded-proto", "https")
        hostname = f"{scheme}://{forwarded}"
    else:
        hostname = str(request.base_url).rstrip("/")
    return {
        "message": f"hello! please use this hostname: {hostname}",
        "phase": "01_bootstrap",
    }


@app.get("/api/health")
def health():
    return {"ok": True}

@app.post("/api/ping-llm", response_model=PingResponse)
def ping_llm(payload: PingRequest):
    api_key = os.getenv("OPENAI_API_KEY")
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    if not api_key:
        logger.warning("OPENAI_API_KEY not set; falling back to fake response")
        return PingResponse(reply="(fake) LLMキー未設定のためダミー応答です。", mode="fake")
    logger.info("calling OpenAI model=%s", model)
    llm = ChatOpenAI(model=model, api_key=api_key, temperature=0)
    out = llm.invoke([{"role":"user","content": payload.prompt}])
    return PingResponse(reply=str(out.content), mode="live")
