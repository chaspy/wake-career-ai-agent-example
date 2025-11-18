"""WAKE Media の公開記事を WordPress REST API 経由でまとめて取得するツール。"""

from __future__ import annotations

import argparse
import datetime as dt
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

import requests
import yaml
from bs4 import BeautifulSoup
from markdownify import markdownify as md

BASE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_OUT_DIR = BASE_DIR / "data" / "wake_articles"
DEFAULT_WORDPRESS_BASE = "https://632664c5972bfba1.main.jp"
PUBLIC_MEDIA_BASE = "https://wake-career.jp/media"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fetch multiple WAKE Media articles via WordPress REST API")
    parser.add_argument("--wp-base", default=DEFAULT_WORDPRESS_BASE, help="WordPress base URL")
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR), help="Directory to store Markdown snapshots")
    parser.add_argument("--per-page", type=int, default=50, help="Posts fetched per request (max 100)")
    parser.add_argument("--max-pages", type=int, default=None, help="Stop after this many pages")
    parser.add_argument("--since", help="Only fetch posts published after this ISO date (YYYY-MM-DD)")
    parser.add_argument("--until", help="Only fetch posts published before this ISO date (YYYY-MM-DD)")
    parser.add_argument("--limit", type=int, help="Maximum number of posts to process")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing Markdown files")
    parser.add_argument("--categories", nargs="*", type=int, help="Restrict to WordPress category IDs")
    parser.add_argument("--slugs", nargs="*", help="Fetch specific slugs (bypasses pagination)")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    session = requests.Session()
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    if args.slugs:
        posts = [fetch_post_by_slug(session, args.wp_base, slug) for slug in args.slugs]
    else:
        posts = list(
            paginate_posts(
                session=session,
                base=args.wp_base,
                per_page=min(args.per_page, 100),
                max_pages=args.max_pages,
                since=args.since,
                until=args.until,
                categories=args.categories,
                limit=args.limit,
            )
        )

    if not posts:
        print("[fetch] no posts matched the criteria", file=sys.stderr)
        return

    tag_map = fetch_taxonomy(session, args.wp_base, "tags")
    category_map = fetch_taxonomy(session, args.wp_base, "categories")

    written = 0
    skipped = 0
    for post in posts:
        slug = post["slug"]
        filename = out_dir / f"{slug}.md"
        if filename.exists() and not args.overwrite:
            skipped += 1
            continue
        markdown_body = md(post["content"]["rendered"]).strip()
        title = strip_html(post["title"]["rendered"])
        tags = [tag_map.get(tag_id) for tag_id in post.get("tags", [])]
        tags = [tag for tag in tags if tag]
        category = None
        for cat_id in post.get("categories", []):
            category = category_map.get(cat_id)
            if category:
                break
        front_matter = {
            "title": title,
            "slug": slug,
            "source_url": f"{PUBLIC_MEDIA_BASE}/{slug}",
            "published": post["date"][:10],
            "tags": tags,
            "category": category,
            "wp_id": post["id"],
            "wp_link": post["link"],
            "modified": post["modified"][:19].replace("T", " "),
        }
        yaml_dump = yaml.safe_dump(front_matter, allow_unicode=True, sort_keys=False)
        filename.write_text(f"---\n{yaml_dump}---\n\n{markdown_body}\n", encoding="utf-8")
        written += 1
        print(f"[fetch] wrote {filename}")

    print(f"[fetch] completed. written={written} skipped={skipped}")


def paginate_posts(
    session: requests.Session,
    base: str,
    per_page: int,
    max_pages: Optional[int],
    since: Optional[str],
    until: Optional[str],
    categories: Optional[List[int]],
    limit: Optional[int],
) -> Iterable[Dict[str, Any]]:
    page = 1
    seen = 0
    params: Dict[str, Any] = {"per_page": per_page, "page": page, "orderby": "date", "order": "desc"}
    if since:
        params["after"] = normalize_date(since)
    if until:
        params["before"] = normalize_date(until, end_of_day=True)
    if categories:
        params["categories"] = ",".join(str(c) for c in categories)

    while True:
        params["page"] = page
        resp = session.get(f"{base}/wp-json/wp/v2/posts", params=params, timeout=20)
        if resp.status_code == 400 and "rest_post_invalid_page_number" in resp.text:
            break
        resp.raise_for_status()
        data = resp.json()
        if not data:
            break
        for post in data:
            yield post
            seen += 1
            if limit and seen >= limit:
                return
        page += 1
        if max_pages and page > max_pages:
            break


def fetch_post_by_slug(session: requests.Session, base: str, slug: str) -> Dict[str, Any]:
    resp = session.get(f"{base}/wp-json/wp/v2/posts", params={"slug": slug}, timeout=20)
    resp.raise_for_status()
    posts = resp.json()
    if not posts:
        raise SystemExit(f"slug not found: {slug}")
    return posts[0]


def fetch_taxonomy(session: requests.Session, base: str, name: str) -> Dict[int, str]:
    page = 1
    items: Dict[int, str] = {}
    while True:
        resp = session.get(
            f"{base}/wp-json/wp/v2/{name}",
            params={"per_page": 100, "page": page},
            timeout=20,
        )
        if resp.status_code == 400 and "rest_" in resp.text:
            break
        resp.raise_for_status()
        data = resp.json()
        if not data:
            break
        for item in data:
            items[item["id"]] = item.get("slug") or item.get("name")
        page += 1
    return items


def normalize_date(value: str, *, end_of_day: bool = False) -> str:
    try:
        dt_obj = dt.datetime.fromisoformat(value)
    except ValueError:
        dt_obj = dt.datetime.strptime(value, "%Y-%m-%d")
    if end_of_day and dt_obj.time() == dt.time(0, 0, 0):
        dt_obj = dt_obj.replace(hour=23, minute=59, second=59)
    if dt_obj.tzinfo is None:
        dt_obj = dt_obj.replace(tzinfo=dt.timezone.utc)
    return dt_obj.isoformat()


def strip_html(value: str) -> str:
    return BeautifulSoup(value, "html.parser").get_text(separator=" ", strip=True)


if __name__ == "__main__":
    main()
