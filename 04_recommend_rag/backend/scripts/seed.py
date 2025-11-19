"""WAKE Career 記事を読み込み、VectorStore と記事インデックスを更新する。"""

from __future__ import annotations

import argparse
import os
from pathlib import Path

import sys

BASE_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = BASE_DIR.parent
ENV_FILES = [BASE_DIR / ".env", REPO_ROOT / ".env"]
for env_file in ENV_FILES:
    if env_file.exists():
        for raw in env_file.read_text().splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip())

if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from app.config import get_settings
from app.db import database
from app.rag import ingest
from app.rag.vectorstore import VectorStoreError, persist_documents

DEFAULT_ARTICLE_DIR = BASE_DIR / "data" / "wake_articles"
DEFAULT_VECTOR_DIR = BASE_DIR / "data" / "vectorstore"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Seed WAKE articles into the vectorstore")
    parser.add_argument("--articles-dir", default=str(DEFAULT_ARTICLE_DIR), help="Markdown の格納ディレクトリ")
    parser.add_argument("--vector-dir", default=str(DEFAULT_VECTOR_DIR), help="VectorStore の保存先")
    parser.add_argument("--mode", choices=["fake", "live"], help="強制的に MODE を上書き")
    parser.add_argument("--db-mode", choices=["sqlite", "json"], help="DBモードを上書き")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.mode:
        os.environ["MODE"] = args.mode
    if args.db_mode:
        os.environ["DB_MODE"] = args.db_mode
    # 設定を再読み込み
    get_settings.cache_clear()
    settings = get_settings()

    articles_dir = Path(args.articles_dir)
    vector_dir = Path(args.vector_dir)

    documents, metadata = ingest.prepare_documents(articles_dir)
    if not documents:
        print(f"[seed] {articles_dir} に Markdown が見つかりません。fetch スクリプトで記事を追加してください。")
        return

    try:
        result = persist_documents(documents, vector_dir)
        database.save_article_index(metadata)
        print(
            f"[seed] {len(metadata)} 件の記事を {result['backend']} で保存しました。path={result['path']} MODE={settings.mode}"
        )
    except VectorStoreError as exc:
        raise SystemExit(f"VectorStore の生成に失敗しました: {exc}") from exc


if __name__ == "__main__":
    main()
