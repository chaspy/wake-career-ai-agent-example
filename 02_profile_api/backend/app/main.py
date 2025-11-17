from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from pathlib import Path
import json

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

app = FastAPI(title="02_profile_api")

@app.get("/api/health")
def health():
    return {"ok": True, "phase": "02_profile_api"}

@app.get("/api/profile", response_model=ProfileResponse)
def get_profile():
    if not DATA_FILE.exists():
        raise HTTPException(status_code=404, detail="profile not set")
    data = json.loads(DATA_FILE.read_text())
    return ProfileResponse(**data)

@app.put("/api/profile", response_model=ProfileResponse)
def upsert_profile(payload: Profile):
    DATA_FILE.write_text(payload.model_dump_json(indent=2, ensure_ascii=False))
    return ProfileResponse(**payload.model_dump())
