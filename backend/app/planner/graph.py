"""LangGraph を用いたキャリアプランニングフロー。"""

from __future__ import annotations

from typing import Any, Dict, List, MutableMapping, Optional, TypedDict

from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph
from pydantic import BaseModel, Field

from app.config import get_runtime_mode, get_settings
from app.models import (
    JobSummary,
    PlanCareerOption,
    PlanReport,
    Profile,
    Recommendation,
)


class PlannerState(TypedDict, total=False):
    profile: Optional[Dict[str, Any]]
    recommendations: List[Dict[str, Any]]
    jobs: List[Dict[str, Any]]
    plan: Dict[str, Any]
    logs: List[str]


class LLMPlanOption(BaseModel):
    title: str
    rationale: str
    citation: Optional[str] = None
    distance: str
    risk: str
    next: str = Field(..., description="次に取るべき行動を 1 文で記載")


class LLMPlanResponse(BaseModel):
    profileInsights: List[str] = Field(min_length=1, max_length=6)
    careerOptions: List[LLMPlanOption] = Field(min_length=1, max_length=4)
    learning: List[str] = Field(min_length=1, max_length=6)
    actions: List[str] = Field(min_length=1, max_length=6)
    selfCheck: List[str] = Field(min_length=1, max_length=6)


def build_planner_graph():
    graph = StateGraph(PlannerState)
    graph.add_node("prepare", _prepare_state)
    graph.add_node("call_model", _call_model)
    graph.add_node("finalize", _finalize)
    graph.set_entry_point("prepare")
    graph.add_edge("prepare", "call_model")
    graph.add_edge("call_model", "finalize")
    graph.add_edge("finalize", "__end__")
    return graph.compile()


def _prepare_state(state: PlannerState) -> PlannerState:
    logs = list(state.get("logs") or [])
    profile = _ensure_profile_dict(state.get("profile"))
    recs = _ensure_dict_list(state.get("recommendations"))
    jobs = _ensure_dict_list(state.get("jobs"))
    logs.append(f"[planner] inputs: recs={len(recs)} jobs={len(jobs)}")
    return {
        "profile": profile,
        "recommendations": recs,
        "jobs": jobs,
        "logs": logs,
    }


def _call_model(state: PlannerState) -> PlannerState:
    settings = get_settings()
    logs = list(state.get("logs") or [])
    mode = get_runtime_mode()

    plan_dict: Optional[Dict[str, Any]] = None
    if mode == "live" and settings.openai_api_key:
        plan_dict = _run_live_model(
            state["profile"],
            state["recommendations"],
            state["jobs"],
        )
        if plan_dict:
            logs.append("[planner] live LangGraph run succeeded")
    if not plan_dict:
        plan_dict = _build_offline_plan(
            state["profile"],
            state["recommendations"],
            state["jobs"],
        )
        logs.append("[planner] fallback to offline template (MODE=fake or live error)")

    new_state = dict(state)
    new_state["plan"] = plan_dict
    new_state["logs"] = logs
    return new_state  # type: ignore[return-value]


def _finalize(state: PlannerState) -> PlannerState:
    plan_dict = state.get("plan")
    if not plan_dict:
        plan_dict = PlanReport().model_dump()
    new_state = dict(state)
    new_state["plan"] = plan_dict
    return new_state  # type: ignore[return-value]


def _run_live_model(
    profile: Optional[Dict[str, Any]],
    recs: List[Dict[str, Any]],
    jobs: List[Dict[str, Any]],
) -> Optional[Dict[str, Any]]:
    settings = get_settings()
    if not settings.openai_api_key:
        return None

    llm = ChatOpenAI(
        model=settings.openai_model,
        temperature=0.2,
        api_key=settings.openai_api_key,
    )
    parser = PydanticOutputParser(pydantic_object=LLMPlanResponse)
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "あなたはキャリアコーチです。必ず JSON 形式で応答し、{format_instructions} に従ってください。",
            ),
            (
                "human",
                "以下のプロフィール・推薦記事・求人サマリを参考に、学習/行動プランを提案してください。\n"
                "プロフィール:\n{profile}\n\n"
                "推薦記事:\n{recommendations}\n\n"
                "求人サマリ:\n{jobs}\n\n"
                "キャリアオプションは距離(短/中/長)とリスク(低/中/高)を必ず含めてください。"
                "learning/actions/self_check は箇条書き形式で 2-4 件ずつ提示してください。",
            ),
        ]
    )
    profile_text = _profile_to_text(profile)
    reco_text = _recommendations_to_text(recs)
    job_text = _jobs_to_text(jobs)
    chain = prompt | llm | parser
    try:
        response = chain.invoke(
            {
                "profile": profile_text,
                "recommendations": reco_text,
                "jobs": job_text or "求人データなし",
                "format_instructions": parser.get_format_instructions(),
            }
        )
    except Exception as exc:  # pragma: no cover
        print(f"[planner] live call failed: {exc}")
        return None
    plan = PlanReport(**response.model_dump())
    return plan.model_dump()


def _build_offline_plan(
    profile: Optional[Dict[str, Any]],
    recs: List[Dict[str, Any]],
    jobs: List[Dict[str, Any]],
) -> Dict[str, Any]:
    profile = profile or {}
    recs = recs or []
    jobs = jobs or []

    current = profile.get("current_role") or "現職"
    years = profile.get("years") or 0
    target = profile.get("target_role") or "次のロール"
    skills = ", ".join(profile.get("skills") or [])
    interests = ", ".join(profile.get("interests") or [])

    profile_insights = [
        f"あなたは「{current}」として {years} 年の経験を持ち、目標は「{target}」。",
        f"主力スキルは {skills or '（未入力）'}、興味は {interests or '（未入力）'}。",
        "これらを踏まえ、次の3つの進路オプションを提示します。",
    ]

    rec1 = recs[0] if recs else {}
    rec2 = recs[1] if len(recs) > 1 else {}
    rec3 = recs[2] if len(recs) > 2 else {}

    job_titles = [job.get("title") for job in jobs if job.get("title")]
    top_job = job_titles[0] if job_titles else "注目求人"

    options = [
        PlanCareerOption(
            title="オプション1: 既存領域を磨きミドルリードへ",
            rationale="現在の強みを軸にSLOやチーム成果を短期で出し、信頼を高めるルート。",
            citation=_primary_citation(rec1),
            distance="短",
            risk="低",
            next=f"今週中に {current} としての強みをまとめ、{top_job} に通じる成果指標を整理する。",
        ),
        PlanCareerOption(
            title="オプション2: 組織/プロダクト両面のリードへ",
            rationale="採用・評価・技術負債の設計を担い、10→100 フェーズの難題を解くルート。",
            citation=_primary_citation(rec2),
            distance="中",
            risk="中",
            next="90日ロードマップを作り、技術負債と採用ニーズを可視化する。",
        ),
        PlanCareerOption(
            title="オプション3: AI/RAG 領域へピボットし市場価値を上げる",
            rationale="生成AI×プロダクトに軸足を移し、MLOpsやRAG基盤づくりで差別化するルート。",
            citation=_primary_citation(rec3),
            distance="中〜長",
            risk="中",
            next="小規模なRAG/LLM PoCを2週間で構築し、コストとSLOをレポートする。",
        ),
    ]

    learning = [
        _learning_from_rec(rec1, "推薦1"),
        _learning_from_rec(rec2, "推薦2"),
        "週1回アウトプット（社内LT/ブログ）で学びを共有する。",
    ]

    actions = [
        f"{(profile.get('skills') or ['主力スキル'])[0]} を使ったミニプロジェクトを今月内にリリースする。",
        "推薦記事の引用で3分ピッチを作成し録音セルフレビューする。",
        "求人要件を参照し不足スキルを3つ洗い出して学習ブロックを入れる。",
    ]

    self_check = [
        "1週目: 推薦記事1本の引用メモを作成できたか？",
        "2週目: ミニプロジェクトを公開できたか？",
        "4週目: 受けたい求人2社に合わせ履歴書を更新したか？",
    ]

    report = PlanReport(
        profileInsights=profile_insights,
        careerOptions=options,
        learning=[item for item in learning if item],
        actions=actions,
        selfCheck=self_check,
    )
    return report.model_dump()


def _profile_to_text(profile: Optional[Dict[str, Any]]) -> str:
    if not profile:
        return "name=未入力, role=未入力"
    skills = ", ".join(profile.get("skills") or [])
    interests = ", ".join(profile.get("interests") or [])
    return (
        f"name={profile.get('name', '未入力')}, "
        f"current={profile.get('current_role', '未入力')}, "
        f"target={profile.get('target_role', '未入力')}, "
        f"years={profile.get('years', 0)}, "
        f"skills={skills or '未入力'}, "
        f"interests={interests or '未入力'}"
    )


def _recommendations_to_text(recs: List[Dict[str, Any]]) -> str:
    lines: List[str] = []
    for idx, rec in enumerate(recs[:5], start=1):
        reasons = "; ".join(rec.get("reasons") or [])
        lines.append(
            f"[Reco{idx}] {rec.get('title')} ({rec.get('url')}) | reasons: {reasons}"
        )
    return "\n".join(lines) or "推薦なし"


def _jobs_to_text(jobs: List[Dict[str, Any]]) -> str:
    lines: List[str] = []
    for idx, job in enumerate(jobs[:5], start=1):
        lines.append(
            f"[Job{idx}] {job.get('title')} @ {job.get('company')} ({job.get('url')})"
        )
    return "\n".join(lines)


def _learning_from_rec(rec: Dict[str, Any], fallback: str) -> str:
    if not rec:
        return f"{fallback} で得た学びを 3 点メモする。"
    title = rec.get("title", fallback)
    url = rec.get("url") or _primary_citation(rec)
    url_suffix = f"（URL: {url}）" if url else ""
    return f"「{title}」を読み、引用と学びを3つ整理する{url_suffix}"


def _primary_citation(rec: Dict[str, Any]) -> Optional[str]:
    citations = rec.get("citations") or []
    if citations and isinstance(citations, list):
        first = citations[0]
        if isinstance(first, MutableMapping):
            return first.get("source_url")
    return rec.get("url")


def _ensure_profile_dict(profile: Optional[Any]) -> Optional[Dict[str, Any]]:
    if profile is None:
        return None
    if isinstance(profile, dict):
        return profile
    if hasattr(profile, "model_dump"):
        return profile.model_dump()
    return dict(profile)


def _ensure_dict_list(items: Optional[Any]) -> List[Dict[str, Any]]:
    if not items:
        return []
    normalized: List[Dict[str, Any]] = []
    for item in items:
        if isinstance(item, dict):
            normalized.append(item)
        elif hasattr(item, "model_dump"):
            normalized.append(item.model_dump())
        else:
            normalized.append(dict(item))
    return normalized
