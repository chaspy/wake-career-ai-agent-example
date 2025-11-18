# 03_articles_ingest

前フェーズとの差分: 01/02 のプロフィール管理＋LLM アドバイスを残したまま、記事インジェストと RAG 推薦を追加。
- `/api/profile` (GET/PUT) … プロフィールの保存/取得。`backend/app/data/profile.json` に永続化。
- `/api/profile/advice` … 保存済みプロフィールをプロンプトに差し込み、fake もしくは OpenAI で回答。
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
- プロフィール: `/api/profile` が JSON を読み書き、`/api/profile/advice` は保存済みプロフィールをプロンプトに入れて ChatOpenAI（キー未設定時は fake テキスト）を叩きます。
- seed: `scripts/seed.py` が markdown をチャンク分割（LangChain TextSplitter）し、FAISS へ保存。OpenAI キーなしは FakeEmbeddings、ありは text-embedding-3-small。
- 推薦: `/api/recommendations` は FAISS の類似検索を叩き、fake 時は固定文言、live 時は ChatOpenAI で理由生成。
- mode/provider: health で `fake/live` を返すので、UI 側で状態表示できます。

## 02→03 のコード差分（解説）
- **データの広がり**: 記事 Markdown を `backend/app/data/articles/` に置き、`seed.py` がチャンク化→FAISS に格納（`RecursiveCharacterTextSplitter` と `FAISS.from_documents`）。ベクトルストアは `index.faiss/index.pkl` で保存・読み込みします（`backend/app/main.py:100-175`）。
- **埋め込みの切替**: `OPENAI_API_KEY` 有無で `OpenAIEmbeddings(text-embedding-3-small)` / `FakeEmbeddings(1536次元)` を動的に選択（`backend/app/main.py:109-112`）。02 では LLM 呼び出しのみだったため、Embedding は新規追加。
- **RAG ルート追加**: `/api/recommendations` が `similarity_search_with_score` を呼び、FAISS の距離スコアを 0〜1 類似度に正規化して返却（`backend/app/main.py:151-176`）。理由文は ChatOpenAI で1文生成、キー未設定時は固定文（`_make_reasons` at 211-221）。
- **プロフィール機能は継承**: `/api/profile` と `/api/profile/advice` は 02 のまま形を保ちつつ保存先が `data/profile.json` に変更。Fake/Live 両モードで同じプロンプトビルダーを使用（`backend/app/main.py:125-189, 224-243`）。デフォルトプロフィールを同梱したためクローン直後に叩けます。
- **フロント統合**: 02 のプロフィール＋アドバイス UI を残したまま、記事一覧（横並び）と RAG 推薦カードを同一ページに配置。ボタンにローディング表示を付与し、類似度スコアが 0〜1 で見えるようにしています（`frontend/src/main.tsx` 全体、`style.css` の `list.horizontal`, `reco-grid` など）。
- **変わっていないもの**: プロファイルスキーマ・アドバイスのプロンプト設計・Fake 回答の方針は 02 と同一。FastAPI の型定義や Pydantic モデルの構造もほぼ踏襲しています。

## フロントの流れ
1. プロフィールを入力して保存 → `/api/profile` PUT。
2. 「LLM にキャリア相談」で `/api/profile/advice` を叩き、保存済みプロフィールを差し込んだ回答を表示。
3. `/api/articles` でリスト化 → クリックで `/api/articles/{slug}` 詳細表示。
4. クエリ入力後「おすすめを取得」→ `/api/recommendations` POST → スコア・理由つきカード表示。
