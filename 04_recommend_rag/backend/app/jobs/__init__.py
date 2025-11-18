"""Job fetchers with agentic refinement loop."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable, List, Optional
from urllib.parse import urlencode

import requests
from bs4 import BeautifulSoup
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from app.config import get_settings
from app.models import JobSummary, Profile

WANTEDLY_URL = "https://www.wantedly.com/projects"
REMOTIVE_URL = "https://remotive.com/api/remote-jobs"
FETCH_TIMEOUT = 8  # seconds, keep UI responsive
MAX_JOB_ITERATIONS = 3


@dataclass
class JobAgentResult:
    jobs: List[JobSummary]
    sources: List[str]
    queries: List[str]


class JobEvaluationItem(BaseModel):
    job_id: str
    score: float = Field(ge=0, le=1)
    reason: str


class JobEvaluationResponse(BaseModel):
    evaluations: List[JobEvaluationItem]
    should_refine: bool = False
    refine_query: Optional[str] = None


def search_jobs(profile: Optional[Profile], query: Optional[str], location: Optional[str], limit: int) -> JobAgentResult:
    profile = profile or Profile(
        name="Guest",
        years=0,
        current_role="",
        target_role="",
        skills=[],
        interests=[],
    )
    current_query = (query or "").strip() or _build_query_from_profile(profile)
    queries_tried: list[str] = []
    collected_sources: set[str] = set()
    last_candidates: list[JobSummary] = []

    for attempt in range(MAX_JOB_ITERATIONS):
        queries_tried.append(current_query)
        candidates = _fetch_jobs(current_query, location, limit)
        if not candidates:
            if attempt == 0:
                current_query = "エンジニア"
                continue
            break
        last_candidates = candidates
        collected_sources.update(job.source for job in candidates)
        evaluation = _evaluate_jobs(profile, current_query, candidates)
        ranked = _rank_jobs(candidates, evaluation, limit)
        if ranked:
            return JobAgentResult(jobs=ranked, sources=sorted(collected_sources), queries=queries_tried)
        refine_query = evaluation.refine_query if evaluation.should_refine else None
        if refine_query and refine_query not in queries_tried:
            current_query = refine_query
            continue
        fallback_query = _fallback_refine_query(current_query, profile)
        if fallback_query and fallback_query not in queries_tried:
            current_query = fallback_query
            continue
        break

    return JobAgentResult(jobs=last_candidates[:limit], sources=sorted(collected_sources), queries=queries_tried)


def _fetch_jobs(query: Optional[str], location: Optional[str], limit: int) -> list[JobSummary]:
    aggregated: list[JobSummary] = []
    for fetcher in (_fetch_wantedly, _fetch_remotive):
        try:
            aggregated.extend(fetcher(query=query, location=location, limit=limit * 2))
        except Exception as exc:  # pragma: no cover
            print(f"[jobs] {fetcher.__name__} failed: {exc}")
    if not aggregated:
        return []
    aggregated.sort(key=_job_sort_key, reverse=True)
    unique: list[JobSummary] = []
    seen: set[str] = set()
    for job in aggregated:
        if job.url in seen:
            continue
        if query and not _matches_keyword(job, query):
            continue
        seen.add(job.url)
        unique.append(job)
        if len(unique) >= limit:
            break
    if len(unique) < limit:
        for job in aggregated:
            if job.url in seen:
                continue
            seen.add(job.url)
            unique.append(job)
            if len(unique) >= limit:
                break
    return unique


def _job_sort_key(job: JobSummary):
    if job.published_at:
        try:
            return datetime.fromisoformat(job.published_at.replace("Z", "+00:00")).astimezone(timezone.utc)
        except ValueError:
            return datetime.min.replace(tzinfo=timezone.utc)
    return datetime.min.replace(tzinfo=timezone.utc)


def _matches_keyword(job: JobSummary, query: str) -> bool:
    text = " ".join(filter(None, [job.title, job.company, job.snippet or ""])).lower()
    tokens = [token.lower() for token in query.split() if token]
    if not tokens:
        return True
    hits = sum(1 for token in tokens if token in text)
    return hits >= 1


def _evaluate_jobs(profile: Profile, query: str, jobs: list[JobSummary]) -> JobEvaluationResponse:
    settings = get_settings()
    if settings.mode == "live" and settings.openai_api_key:
        llm = ChatOpenAI(
            model=settings.openai_model,
            temperature=0,
            api_key=settings.openai_api_key,
        )
        parser = PydanticOutputParser(pydantic_object=JobEvaluationResponse)
        job_text = "\n".join(
            f"id: {job.id}\ntitle: {job.title}\ncompany: {job.company}\nlocation: {job.location}\nsummary: {job.snippet}" for job in jobs
        )
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "あなたはキャリアエージェントです。プロフィールや希望に合う求人のみ高く評価し、JSON で返答してください。",
                ),
                (
                    "human",
                    "プロフィール: {profile}\n検索クエリ: {query}\n候補求人:\n{jobs}\n"
                    "各求人を0-1のスコアで評価し、必要なら refine_query で検索キーワードを提案してください。"
                    "出力は {format_instructions} に従ってください。",
                ),
            ]
        )
        chain = prompt | llm | parser
        try:
            return chain.invoke(
                {
                    "profile": _format_profile(profile),
                    "query": query,
                    "jobs": job_text,
                    "format_instructions": parser.get_format_instructions(),
                }
            )
        except Exception as exc:  # pragma: no cover
            print(f"[jobs] llm evaluation failed: {exc}")
    return _offline_evaluate(profile, query, jobs)


def _offline_evaluate(profile: Profile, query: str, jobs: list[JobSummary]) -> JobEvaluationResponse:
    keywords = [*(profile.skills or []), *(profile.interests or []), profile.target_role or "", profile.current_role or "", query]
    keywords = [token.lower() for token in keywords if token]
    evaluations: list[JobEvaluationItem] = []
    best_token = None
    for job in jobs:
        text = " ".join(filter(None, [job.title, job.snippet or "", job.company or ""])).lower()
        hits = sum(1 for token in keywords if token in text)
        score = min(0.2 + hits * 0.2, 0.95)
        evaluations.append(JobEvaluationItem(job_id=job.id, score=score, reason=f"keyword hits: {hits}"))
        if hits == 0 and not best_token:
            best_token = job.title.split(" ")[0]
    should_refine = all(item.score < 0.6 for item in evaluations)
    refine_query = None
    if should_refine:
        refine_query = (keywords[0] if keywords else query or "エンジニア")
    return JobEvaluationResponse(evaluations=evaluations, should_refine=should_refine, refine_query=refine_query)


def _rank_jobs(jobs: list[JobSummary], evaluation: JobEvaluationResponse, limit: int) -> list[JobSummary]:
    scores = {item.job_id: item.score for item in evaluation.evaluations}
    if not scores:
        return []
    ranked = sorted(jobs, key=lambda job: scores.get(job.id, 0), reverse=True)
    filtered = [job for job in ranked if scores.get(job.id, 0) >= 0.6]
    return filtered[:limit]


def _build_query_from_profile(profile: Profile) -> str:
    parts = [profile.target_role, profile.current_role]
    parts.extend(profile.skills[:2])
    return " ".join(part for part in parts if part) or "エンジニア"


def _fallback_refine_query(current_query: str, profile: Profile) -> Optional[str]:
    tokens = current_query.split()
    if profile.skills:
        for skill in profile.skills:
            if skill not in tokens:
                return f"{skill} エンジニア"
    if profile.interests:
        for interest in profile.interests:
            if interest not in tokens:
                return f"{interest}" 
    return None


def _fetch_wantedly(query: Optional[str], location: Optional[str], limit: int) -> list[JobSummary]:
    params = {"type": "recent"}
    search_terms = " ".join(part for part in [query, location] if part)
    if search_terms:
        params["keyword"] = search_terms
    resp = requests.get(WANTEDLY_URL, params=params, timeout=FETCH_TIMEOUT)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    jobs: list[JobSummary] = []
    for script in soup.find_all("script", attrs={"type": "application/ld+json"}):
        raw = script.string
        if not raw:
            continue
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if isinstance(data, dict) and data.get("@type") == "ItemList":
            items: Iterable[dict] = data.get("itemListElement", [])
            for item in items:
                job = item.get("item", {})
                if not isinstance(job, dict):
                    continue
                description = _strip_html(job.get("description", ""))
                location_parts: list[str] = []
                job_location = job.get("jobLocation")
                if isinstance(job_location, dict):
                    address = job_location.get("address")
                    if isinstance(address, dict):
                        for key in ("addressRegion", "addressLocality", "addressCountry"):
                            value = address.get(key)
                            if value:
                                location_parts.append(value)
                jobs.append(
                    JobSummary(
                        id=str(job.get("@id") or job.get("url") or job.get("identifier", {}).get("value") or len(jobs)),
                        title=job.get("title", "Wantedly Job"),
                        company=(job.get("hiringOrganization") or {}).get("name"),
                        url=job.get("url", WANTEDLY_URL),
                        location=", ".join(location_parts) if location_parts else None,
                        published_at=_normalize_datetime(job.get("datePosted")),
                        snippet=description[:400] if description else None,
                        source="wantedly",
                    )
                )
    return jobs[: limit * 2]


def _fetch_remotive(query: Optional[str], location: Optional[str], limit: int) -> list[JobSummary]:
    params = {}
    if query:
        params["search"] = query
    if location:
        params["location"] = location
    resp = requests.get(REMOTIVE_URL, params=params, timeout=FETCH_TIMEOUT)
    resp.raise_for_status()
    payload = resp.json()
    jobs_data = payload.get("jobs", [])
    jobs: list[JobSummary] = []
    for job in jobs_data[: limit * 2]:
        description = _strip_html(job.get("description", ""))
        jobs.append(
            JobSummary(
                id=str(job.get("id")),
                title=job.get("title", "Remotive Job"),
                company=job.get("company_name"),
                url=job.get("url", REMOTIVE_URL),
                location=job.get("candidate_required_location") or job.get("job_type"),
                published_at=_normalize_datetime(job.get("publication_date")),
                snippet=description[:400] if description else None,
                source="remotive",
            )
        )
    return jobs[: limit * 2]


def _strip_html(value: Optional[str]) -> str:
    if not value:
        return ""
    soup = BeautifulSoup(value, "html.parser")
    return soup.get_text(" ", strip=True)


def _normalize_datetime(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        else:
            dt = dt.astimezone(timezone.utc)
    except ValueError:
        return None
    return dt.isoformat()


def _format_profile(profile: Profile) -> str:
    return (
        f"name: {profile.name}\nexperience: {profile.years} years\n"
        f"current_role: {profile.current_role}\ntarget_role: {profile.target_role}\n"
        f"skills: {', '.join(profile.skills or [])}\ninterests: {', '.join(profile.interests or [])}"
    )
