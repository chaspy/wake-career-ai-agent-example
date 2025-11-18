# 03_articles_ingest

前フェーズとの差分: プロフィールに加え、記事の ingest/一覧/詳細を追加（RAGなし）。
- `/api/articles` で Markdown 記事の一覧
- `/api/articles/{slug}` で本文取得
- サンプル記事は `backend/app/data/articles/sample.md`

## 起動手順（uv sync 統一）
```bash
cd 03_articles_ingest

# backend 依存（uv sync が .venv を自動作成）
cd backend && uv sync && cd ..

# frontend 依存
cd frontend && npm install && cd ..

# 開発サーバ起動（デフォルト: backend 38089 / frontend 35073）
BACKEND_PORT=38089 FRONTEND_PORT=35073 make dev
# ブラウザ: http://localhost:35073
```

記事一覧から選択して詳細が表示されればセットアップ完了です。ポートが埋まっている場合は環境変数で上書きしてください。
