"""Pydantic および SQLAlchemy モデル定義。"""

from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field
from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.dialects.sqlite import JSON as SQLiteJSON
from sqlalchemy.orm import Mapped, declarative_base, mapped_column

Base = declarative_base()


class ProfileRecord(Base):
    __tablename__ = "profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    years: Mapped[int] = mapped_column(Integer, default=0)
    current_role: Mapped[str] = mapped_column(String(255))
    target_role: Mapped[str] = mapped_column(String(255))
    skills: Mapped[list[str]] = mapped_column(SQLiteJSON, default=list)
    interests: Mapped[list[str]] = mapped_column(SQLiteJSON, default=list)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    def to_schema(self) -> "ProfileResponse":
        return ProfileResponse(
            name=self.name,
            years=self.years,
            current_role=self.current_role,
            target_role=self.target_role,
            skills=self.skills or [],
            interests=self.interests or [],
            notes=self.notes,
            updated_at=self.updated_at.isoformat(),
        )


class FeedbackRecord(Base):
    __tablename__ = "feedback"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    article_id: Mapped[str] = mapped_column(String(255), index=True)
    liked: Mapped[bool] = mapped_column(Boolean, default=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class ArticleIndexRecord(Base):
    __tablename__ = "article_index"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slug: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(255))
    source_url: Mapped[str] = mapped_column(String(500))
    tags: Mapped[list[str]] = mapped_column(SQLiteJSON, default=list)
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    category: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)


class HealthResponse(BaseModel):
    ok: bool = Field(default=True, description="APIが稼働しているかどうか")
    mode: Literal["fake", "live"] = Field(default="fake", description="推論モード")


class Profile(BaseModel):
    name: str
    years: int = Field(ge=0)
    current_role: str
    target_role: str
    skills: list[str] = Field(default_factory=list)
    interests: list[str] = Field(default_factory=list)
    notes: Optional[str] = None


class ProfileResponse(Profile):
    updated_at: Optional[str] = None


class ArticleMetadata(BaseModel):
    slug: str
    title: str
    source_url: str
    tags: list[str] = Field(default_factory=list)
    category: Optional[str] = None
    published: Optional[str] = None


class ArticleSummary(BaseModel):
    slug: str
    title: str
    source_url: str
    published: Optional[str] = None
    tags: list[str] = Field(default_factory=list)
    category: Optional[str] = None


class ArticleDetail(ArticleSummary):
    body: str


class Citation(BaseModel):
    source_url: str
    title: str
    line: Optional[int] = None


class Recommendation(BaseModel):
    id: str
    title: str
    url: str
    score: float
    excerpt: str
    reasons: list[str]
    citations: list[Citation]


class RecommendationRequest(BaseModel):
    profile: Optional[Profile] = None
    query: Optional[str] = None
    top_k: int = Field(default=3, ge=1, le=8)


class RecommendationResponse(BaseModel):
    recommendations: list[Recommendation]
    mode: Literal["fake", "live"]


class JobSummary(BaseModel):
    id: str
    title: str
    company: Optional[str] = None
    url: str
    location: Optional[str] = None
    published_at: Optional[str] = None
    snippet: Optional[str] = None
    source: str


class JobSearchRequest(BaseModel):
    query: Optional[str] = Field(default=None, description="求人検索キーワード")
    location: Optional[str] = Field(default=None, description="勤務地や地域のキーワード")
    limit: int = Field(default=6, ge=1, le=12)


class JobSearchResponse(BaseModel):
    jobs: list[JobSummary]
    sources: list[str]
