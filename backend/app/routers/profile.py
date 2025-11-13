from fastapi import APIRouter, HTTPException, status

from app.db import database
from app.models import Profile, ProfileResponse

router = APIRouter(prefix="/api/profile", tags=["profile"])


@router.get("", response_model=ProfileResponse)
async def get_profile() -> ProfileResponse:
    profile = database.get_profile()
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="profile not set")
    return profile


@router.put("", response_model=ProfileResponse)
async def upsert_profile(payload: Profile) -> ProfileResponse:
    return database.save_profile(payload)
