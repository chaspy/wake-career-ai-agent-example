# 03_articles_ingest

前フェーズとの差分: 記事一覧/詳細に加え、RAG 推薦を本格化（FAISS/Chroma、fake/live 切替）。
- `/api/articles` … Markdown 記事の一覧
- `/api/articles/{slug}` … 記事本文取得
- `/api/recommendations` … ベクトル検索＋ fake/live 理由生成
- サンプル記事: `backend/app/data/articles/sample.md`

## 起動手順（最短）
```bash
cd 03_articles_ingest
make dev   # 初回は内部で uv run / npm install が走ります
```

RAG 用ベクトルストアを作る（初回だけでOK）
```bash
cd 03_articles_ingest/backend && uv sync && uv run python scripts/seed.py && cd ..
cd frontend && npm install && cd ..
make dev
```
デフォルトポート: backend 38089 / frontend 35073。競合時は `BACKEND_PORT` / `FRONTEND_PORT` を上書きしてください。

## 仕組みの要点
- seed: `scripts/seed.py` が markdown をチャンク分割（LangChain TextSplitter）し、FAISS へ保存。OpenAI キーなしは FakeEmbeddings、ありは text-embedding-3-small。
- 推薦: `/api/recommendations` は FAISS の類似検索を叩き、fake 時は固定文言、live 時は ChatOpenAI で理由生成。
- mode/provider: health で `fake/live` を返すので、UI 側で状態表示できます。

## フロントの流れ
1. `/api/articles` でリスト化 → クリックで `/api/articles/{slug}` 詳細表示。
2. クエリ入力後「おすすめを取得」→ `/api/recommendations` POST → スコア・理由つきカード表示。
