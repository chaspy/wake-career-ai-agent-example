import json
import os
import logging
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel

BASE_DIR = Path(__file__).resolve().parents[1]
ENV_FILES = [BASE_DIR / ".env", BASE_DIR.parent / ".env"]
for env_file in ENV_FILES:
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip())

DATA_FILE = Path(__file__).resolve().parent / "profile.json"

class Profile(BaseModel):
    name: str
    years: int
    current_role: str
    target_role: str
    skills: list[str] = []
    interests: list[str] = []
    notes: str | None = None

class ProfileResponse(Profile):
    pass


class AdviceRequest(BaseModel):
    question: str = "次にどんな行動を取れば良いですか？"


class AdviceResponse(BaseModel):
    provider: str
    answer: str


DEFAULT_PROFILE = Profile(
    name="WAKE Guest",
    years=5,
    current_role="Product Generalist",
    target_role="AI Product Manager",
    skills=["Facilitation", "LLM Prompting", "Career Coaching"],
    interests=["WAKE Articles", "1on1", "RAG"],
    notes="初期状態のサンプルプロフィールです。",
)

logger = logging.getLogger(__name__)

app = FastAPI(title="02_profile_api")

@app.get("/")
def root(request: Request):
    forwarded = request.headers.get("x-forwarded-host")
    if forwarded:
        scheme = request.headers.get("x-forwarded-proto", "https")
        hostname = f"{scheme}://{forwarded}"
    else:
        hostname = str(request.base_url).rstrip("/")
    return {"message": f"hello! please use this hostname: {hostname}"}

@app.get("/api/health")
def health():
    return {"ok": True, "phase": "02_profile_api"}

@app.get("/api/profile", response_model=ProfileResponse)
def get_profile():
    return _load_or_create_profile()

@app.put("/api/profile", response_model=ProfileResponse)
def upsert_profile(payload: Profile):
    DATA_FILE.write_text(payload.model_dump_json(indent=2, ensure_ascii=False))
    return ProfileResponse(**payload.model_dump())


def _load_or_create_profile() -> ProfileResponse:
    if not DATA_FILE.exists():
        default = ProfileResponse(**DEFAULT_PROFILE.model_dump())
        DATA_FILE.write_text(default.model_dump_json(indent=2, ensure_ascii=False))
        return default
    data = json.loads(DATA_FILE.read_text())
    return ProfileResponse(**data)


def _build_prompt(profile: ProfileResponse, question: str) -> list[dict[str, str]]:
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
        f"- 目標ロール「{profile.target_role}」に近い案件/記事を週1で調べる\n"
        f"- {profile.current_role}の経験を活かしつつ、{', '.join(keywords[:2]) or '関連分野'}を深堀りする\n"
        f"- 次の行動: {question}"
    )
    return base


def _call_openai(messages: list[dict[str, str]]) -> str:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set")
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    try:
        llm = ChatOpenAI(model=model, api_key=api_key, temperature=0.4)
        res = llm.invoke(
            [
                SystemMessage(content=messages[0]["content"]),
                HumanMessage(content=messages[1]["content"]),
            ]
        )
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"openai error: {e}")
    content = res.content
    if isinstance(content, list):
        content = "".join(
            chunk.get("text", "") if isinstance(chunk, dict) else str(chunk) for chunk in content
        )
    return str(content or "")


@app.post("/api/profile/advice", response_model=AdviceResponse)
def get_profile_advice(payload: AdviceRequest):
    profile = _load_or_create_profile()
    messages = _build_prompt(profile, payload.question)
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        try:
            answer = _call_openai(messages)
            provider = "openai"
        except Exception as exc:  # noqa: BLE001
            logger.warning("OpenAI呼び出しに失敗したためフォールバックします: %s", exc)
            answer = _fake_answer(profile, payload.question)
            provider = "fake"
    else:
        answer = _fake_answer(profile, payload.question)
        provider = "fake"
    return AdviceResponse(provider=provider, answer=answer)
