from fastapi import FastAPI, Request
from pydantic import BaseModel
from langchain_openai import ChatOpenAI
import os

app = FastAPI(title="Bootstrap API")


@app.get("/")
async def root(request: Request) -> dict[str, str]:
    forwarded = request.headers.get("x-forwarded-host")
    if forwarded:
        scheme = request.headers.get("x-forwarded-proto", "https")
        hostname = f"{scheme}://{forwarded}"
    else:
        hostname = str(request.base_url).rstrip("/")
    return {"message": f"hello! please use this hostname: {hostname}"}

class PingRequest(BaseModel):
    prompt: str = "はじめまして！"

class PingResponse(BaseModel):
    reply: str
    mode: str

@app.get("/")
def root():
    return {"ok": True, "message": "01_bootstrap backend"}


@app.get("/api/health")
def health():
    return {"ok": True}

@app.post("/api/ping-llm", response_model=PingResponse)
def ping_llm(payload: PingRequest):
    api_key = os.getenv("OPENAI_API_KEY")
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    if not api_key:
        return PingResponse(reply="(fake) LLMキー未設定のためダミー応答です。", mode="fake")
    llm = ChatOpenAI(model=model, api_key=api_key, temperature=0)
    out = llm.invoke([{"role":"user","content": payload.prompt}])
    return PingResponse(reply=str(out.content), mode="live")
