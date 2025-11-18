# 03_articles_ingest

前フェーズとの差分: 記事一覧/詳細に加えて RAG 推薦を実装。FAISS/Chroma ベースで fake/live 切替。
- `/api/articles` で Markdown 記事の一覧
- `/api/articles/{slug}` で本文取得
- `/api/recommendations` で類似記事推薦（`MODE=fake` ならダミー理由、`MODE=live` なら OpenAI で理由生成）
- サンプル記事は `backend/app/data/articles/sample.md`

## 起動手順（uv sync 統一）
```bash
cd 03_articles_ingest

# backend 依存（uv sync が .venv を自動作成）
cd backend && uv sync && cd ..

# frontend 依存
cd frontend && npm install && cd ..

# ベクトルストアをシード（初回のみ）
cd backend && uv run python scripts/seed.py && cd ..

# 開発サーバ起動（デフォルト: backend 38089 / frontend 35073）
BACKEND_PORT=38089 FRONTEND_PORT=35073 make dev
# ブラウザ: http://localhost:35073 （「おすすめを取得」でRAG動作確認）
```

記事一覧から選択して詳細が表示されればセットアップ完了です。ポートが埋まっている場合は環境変数で上書きしてください。
