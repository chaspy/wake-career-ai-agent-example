"""MODE=fake 向けの簡易レコメンド生成。"""

from __future__ import annotations

from typing import List, Optional

from langchain_core.documents import Document

from app.models import Profile


def offline_answer(documents: List[Document], profile: Optional[Profile], top_k: int = 3) -> list[dict]:
    drafts: list[dict] = []
    target = profile.target_role if profile else "キャリア目標"
    for rank, doc in enumerate(documents[:top_k]):
        excerpt = doc.page_content.strip().split("\n")[0][:360]
        tags = doc.metadata.get("tags") or []
        tag_phrase = "、".join(tags[:3]) if tags else "実践知"
        intro = doc.page_content.strip()[:60]
        reasons = [
            f"スキル補強: {tag_phrase} を扱うこの記事は {target} が直面しがちな課題に対する具体例を提示します。",
            f"実務応用: 冒頭「{intro}…」で始まり、課題→解決手順→振り返りの流れが職場でそのまま試せます。",
            "成果へのつながり: 読後に自分の案件へ転用ポイントを3つメモすることで、翌週の1on1で成果共有がしやすくなります。",
        ]
        drafts.append(
            {
                "slug": doc.metadata.get("slug", f"doc-{rank}"),
                "title": doc.metadata.get("title", "WAKE Article"),
                "url": doc.metadata.get("source_url", ""),
                "excerpt": excerpt or doc.page_content[:360],
                "reasons": reasons,
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
