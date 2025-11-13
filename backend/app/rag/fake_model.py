"""MODE=fake 向けの簡易レコメンド生成。"""

from __future__ import annotations

from typing import List, Optional

from langchain_core.documents import Document

from app.models import Profile


def offline_answer(documents: List[Document], profile: Optional[Profile], top_k: int = 3) -> list[dict]:
    drafts: list[dict] = []
    target = profile.target_role if profile else "キャリア目標"
    for rank, doc in enumerate(documents[:top_k]):
        excerpt = doc.page_content.strip().split("\n")[0][:220]
        tags = doc.metadata.get("tags") or []
        tag_phrase = "、".join(tags[:3]) if tags else "実践知"
        reason = f"{doc.metadata.get('title')} は {target} を目指す際に {tag_phrase} を補強するヒントになります。"
        drafts.append(
            {
                "slug": doc.metadata.get("slug", f"doc-{rank}"),
                "title": doc.metadata.get("title", "WAKE Article"),
                "url": doc.metadata.get("source_url", ""),
                "excerpt": excerpt or doc.page_content[:220],
                "reasons": [reason],
                "citations": [
                    {
                        "source_url": doc.metadata.get("source_url", ""),
                        "title": doc.metadata.get("title", "WAKE Article"),
                        "line": doc.metadata.get("line"),
                    }
                ],
                "score": max(0.9 - rank * 0.1, 0.1),
            }
        )
    return drafts
