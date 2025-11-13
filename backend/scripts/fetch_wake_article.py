"""WAKE Career 記事を Markdown スナップショットとして保存するユーティリティ。"""

from __future__ import annotations

import argparse
import datetime as dt
import re
from pathlib import Path

import requests
import yaml
from bs4 import BeautifulSoup
from markdownify import markdownify as md

BASE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_OUT_DIR = BASE_DIR / "data" / "wake_articles"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fetch a WAKE Career article into Markdown")
    parser.add_argument("--url", required=True, help="WAKE Career 記事のURL")
    parser.add_argument("--slug", help="ファイル名に利用するスラッグ。未指定時はタイトルから生成")
    parser.add_argument("--tags", help="カンマ区切りのタグ")
    parser.add_argument("--category", help="記事カテゴリ")
    parser.add_argument("--published", help="ISO8601形式の公開日 (例: 2024-05-01)")
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR), help="保存先ディレクトリ")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    resp = requests.get(args.url, timeout=20)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")
    title = (soup.find("meta", property="og:title") or soup.find("title"))
    if title is None:
        raise SystemExit("title が取得できませんでした")
    title_text = title.get("content") if title.name == "meta" else title.get_text(strip=True)

    article = soup.find("article") or soup.find("main") or soup.body
    markdown_body = md(str(article)) if article else md(resp.text)
    slug = args.slug or _slugify(title_text)
    tags = _split_tags(args.tags)
    published = args.published or dt.date.today().isoformat()

    front_matter = {
        "title": title_text,
        "source_url": args.url,
        "published": published,
        "tags": tags,
    }
    if args.category:
        front_matter["category"] = args.category

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{slug}.md"
    yaml_dump = yaml.safe_dump(front_matter, allow_unicode=True, sort_keys=False)
    path.write_text(f"---\n{yaml_dump}---\n\n{markdown_body.strip()}\n", encoding="utf-8")
    print(f"[fetch] wrote {path}")


def _slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower())
    return slug.strip("-") or "wake-article"


def _split_tags(raw: str | None) -> list[str]:
    if not raw:
        return []
    return [item.strip() for item in raw.split(",") if item.strip()]


if __name__ == "__main__":
    main()
