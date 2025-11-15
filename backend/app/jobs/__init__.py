"""Job fetchers that aggregate public job feeds."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Iterable, Optional
from urllib.parse import urlencode

import requests
from bs4 import BeautifulSoup

from app.models import JobSummary

WANTEDLY_URL = "https://www.wantedly.com/projects"
REMOTIVE_URL = "https://remotive.com/api/remote-jobs"


def search_jobs(query: Optional[str], location: Optional[str], limit: int) -> list[JobSummary]:
    fetchers = [
        _fetch_wantedly,
        _fetch_remotive,
    ]
    aggregated: list[JobSummary] = []
    for fetcher in fetchers:
        try:
            aggregated.extend(fetcher(query=query, location=location, limit=limit))
        except Exception as exc:  # pragma: no cover - network issues are logged
            print(f"[jobs] {fetcher.__name__} failed: {exc}")
    if not aggregated:
        return []

    def sort_key(job: JobSummary):
        if job.published_at:
            try:
                return datetime.fromisoformat(job.published_at.replace("Z", "+00:00"))
            except ValueError:
                return datetime.min
        return datetime.min

    aggregated.sort(key=sort_key, reverse=True)
    unique: list[JobSummary] = []
    seen: set[str] = set()
    for job in aggregated:
        if job.url in seen:
            continue
        seen.add(job.url)
        unique.append(job)
        if len(unique) >= limit:
            break
    return unique


def _fetch_wantedly(query: Optional[str], location: Optional[str], limit: int) -> list[JobSummary]:
    params = {"type": "recent"}
    search_terms = " ".join(part for part in [query, location] if part)
    if search_terms:
        params["keyword"] = search_terms
    resp = requests.get(WANTEDLY_URL, params=params, timeout=15)
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
    return jobs[:limit]


def _fetch_remotive(query: Optional[str], location: Optional[str], limit: int) -> list[JobSummary]:
    params = {}
    if query:
        params["search"] = query
    if location:
        params["location"] = location
    resp = requests.get(REMOTIVE_URL, params=params, timeout=15)
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
    return jobs[:limit]


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
    except ValueError:
        return None
    return dt.isoformat()
