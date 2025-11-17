"""LangGraph を用いた RAG 推薦フロー。"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, TypedDict

from langchain_core.documents import Document
from langgraph.graph import StateGraph
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

from app.config import get_settings
from app.models import Profile
from app.rag import retriever
from app.rag.fake_model import offline_answer


class RecommendationDraft(TypedDict, total=False):
    slug: str
    title: str
    url: str
    excerpt: str
    reasons: List[str]
    citations: List[Dict[str, Any]]
    score: float


class GraphState(TypedDict, total=False):
    profile: Optional[Profile]
    query: Optional[str]
    search_query: str
    k: int
    quotes: List[Document]
    recs: List[RecommendationDraft]


class LLMRecommendation(BaseModel):
    slug: str = Field(..., description="引用する記事の slug")
    reasons: list[str] = Field(
        ...,
        min_length=3,
        max_length=3,
        description=(
            "推薦理由を3つの異なる観点で。"
            "例: スキル適合・実務応用・キャリア成果など。各 70-120 文字で具体的に書くこと。"
        ),
    )


class LLMResponse(BaseModel):
    summary: str
    recommendations: List[LLMRecommendation]


def build_recommendation_graph():
    graph = StateGraph(GraphState)
    graph.add_node("build_query", _build_query)
    graph.add_node("retrieve", _retrieve)
    graph.add_node("call_model", _call_model)
    graph.add_node("respond", _respond)

    graph.set_entry_point("build_query")
    graph.add_edge("build_query", "retrieve")
    graph.add_edge("retrieve", "call_model")
    graph.add_edge("call_model", "respond")
    graph.add_edge("respond", "__end__")
    return graph.compile()


def _build_query(state: GraphState) -> GraphState:
    profile = state.get("profile")
    if state.get("query"):
        query = state["query"]
    else:
        parts: list[str] = []
        if profile:
            parts.extend(filter(None, [profile.target_role, profile.current_role]))
            parts.extend(profile.skills[:3])
            parts.extend(profile.interests[:3])
        query = " ".join(parts) or "キャリア 成長 WAKE"
    new_state = dict(state)
    new_state["search_query"] = query
    return new_state  # type: ignore[return-value]


def _retrieve(state: GraphState) -> GraphState:
    k = state.get("k") or 3
    retr = retriever.get_retriever(k=k)
    documents = retr.invoke(state["search_query"])
    new_state = dict(state)
    new_state["quotes"] = documents
    return new_state  # type: ignore[return-value]


def _call_model(state: GraphState) -> GraphState:
    documents = state.get("quotes") or []
    k = state.get("k") or 3
    settings = get_settings()
    drafts: List[RecommendationDraft]
    if documents:
        if settings.mode == "live" and settings.openai_api_key:
            drafts = _run_live_model(documents, state.get("profile"), state.get("search_query", ""), k)
            if not drafts:
                drafts = offline_answer(documents, state.get("profile"), k)
        else:
            drafts = offline_answer(documents, state.get("profile"), k)
    else:
        drafts = []
    new_state = dict(state)
    new_state["recs"] = drafts
    return new_state  # type: ignore[return-value]


def _respond(state: GraphState) -> GraphState:
    recs = state.get("recs") or []
    if not recs:
        recs = [
            {
                "slug": "no-data",
                "title": "十分な記事が見つかりませんでした",
                "url": "https://wake-career.jp/",
                "excerpt": "ベクトル検索に一致する記事が見つからなかったため、タグやプロフィールを見直してください。",
                "reasons": ["記事データが不足しているか、検索条件が広すぎます。"],
                "citations": [],
                "score": 0.0,
            }
        ]
    new_state = dict(state)
    new_state["recs"] = recs
    return new_state  # type: ignore[return-value]


def _run_live_model(
    documents: List[Document], profile: Optional[Profile], query: str, top_k: int
) -> List[RecommendationDraft]:
    settings = get_settings()
    if not settings.openai_api_key:
        return []
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.2,
        api_key=settings.openai_api_key,
        base_url=settings.openai_base_url,
    )
    parser = PydanticOutputParser(pydantic_object=LLMResponse)
    profile_text = _format_profile(profile)
    context = "\n\n".join(
        [
            f"slug: {doc.metadata.get('slug')}\ntitle: {doc.metadata.get('title')}\nurl: {doc.metadata.get('source_url')}\nexcerpt: {doc.page_content[:900]}"
            for doc in documents[:top_k]
        ]
    )
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "あなたはキャリアの学習パートナーです。必ず JSON で返し、引用元 slug を recommendations.slug に記載してください。",
            ),
            (
                "human",
                "プロフィール: {profile}\n検索クエリ: {query}\n候補記事:\n{context}\n\n"
                "上記コンテキストのみを使い、最大 {top_k} 件の推薦を JSON で返してください。"
                "各 recommendation で reasons を3つ返してください。"
                "それぞれ異なる観点（例: スキルフィット / 実務での活かし方 / 想定成果やリスク）で 70-120 文字ずつ。"
                "記事の具体的な内容とプロフィール/クエリを必ず結びつけてください。"
                "出力は {format_instructions} に従ってください。",
            ),
        ]
    )
    chain = prompt | llm | parser
    try:
        llm_response = chain.invoke(
            {
                "profile": profile_text,
                "query": query,
                "context": context,
                "top_k": top_k,
                "format_instructions": parser.get_format_instructions(),
            }
        )
    except Exception as exc:  # pragma: no cover
        print(f"[graph] live model failed: {exc}")
        return []

    doc_map = {doc.metadata.get("slug"): doc for doc in documents}
    drafts: List[RecommendationDraft] = []
    for rank, item in enumerate(llm_response.recommendations):
        doc = doc_map.get(item.slug)
        if not doc:
            continue
        drafts.append(
            {
                "slug": doc.metadata.get("slug", f"doc-{rank}"),
                "title": doc.metadata.get("title", "WAKE Article"),
                "url": doc.metadata.get("source_url", ""),
                "excerpt": doc.page_content.strip()[:360],
                "reasons": item.reasons,
                "citations": [
                    {
                        "source_url": doc.metadata.get("source_url", ""),
                        "title": doc.metadata.get("title", "WAKE Article"),
                        "line": doc.metadata.get("line"),
                    }
                ],
                "score": max(0.95 - rank * 0.05, 0.1),
            }
        )
    return drafts


def _format_profile(profile: Optional[Profile]) -> str:
    if not profile:
        return "未入力"
    return (
        f"name={profile.name}, current={profile.current_role}, target={profile.target_role}, "
        f"skills={','.join(profile.skills)}, interests={','.join(profile.interests)}"
    )
