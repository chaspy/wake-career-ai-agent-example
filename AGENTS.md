# AI Agent クイックスタート

- 返答は常に日本語（コードやログは英語のままで可）。
- `.codex/prompts/` や `.claude/commands/` に用意済みのスラッシュコマンドを優先的に再利用。
- 判断に迷ったら必ずユーザに確認し、独断で決めない。
- `git` / `gh` を積極的に使って作業と変更履歴を管理。
- 作業前に本ファイルと `README.md` を読み、最新コードと手順を把握する。
- ルート直下の `backend/` と `frontend/` が完成版（= `05_jobs_and_planning` と同一）、`01`〜`04` はステップ別スナップショット。

## リポジトリ概要（WAKE Career AI Agent Example）

### ステップスナップショット
- `01_bootstrap`: React + FastAPI の最小構成。API/DB なし。
- `02_profile_api`: プロフィール CRUD API を追加。`backend/app/routers/profile.py` が中心。
- `03_articles_ingest`: wake 記事 Markdown とベクトルストアのインジェスト機能を追加。
- `04_recommend_rag`: LangChain ベースの RAG 推薦 API を追加。
- `05_jobs_and_planning`: 求人 + プランニングまで揃った最終形。ルート直下と同じ内容。
- 各ステップを試す場合は対象ディレクトリ以下の `backend/`・`frontend/` のみを起動し、他ステップと混在させない。

### 主要ディレクトリ
- `backend/`: FastAPI サービス本体。`app/routers`, `app/rag/`, `app/db.py`, `app/tests/` などで構成。
- `backend/app/planner/`: LangGraph でプランニングエージェントを構成。`graph.py` がステートマシン、`routers/plan.py` が `/api/plan` を公開。
- `backend/data/`: wake 記事 Markdown、FAISS/Chroma ベクトルストア、SQLite/JSON プロファイルなどワークショップ用データ。
- `backend/scripts/seed.py`: Markdown からベクトルストアを生成するコマンド。`MODE` に応じて Fake/OpenAI Embeddings を切り替え。
- `frontend/`: Vite + React（TypeScript）。UI は `frontend/src`、静的アセットは `frontend/public/`。
- `Makefile`: backend/frontend の同時起動、インストール、テスト、シードをまとめたラッパー。
- `slides.md` / `port.png`: ハンズオン資料および Codespaces でのポート公開手順。

## セットアップと依存準備

1. `.env` が無ければサンプルからコピーし、`OPENAI_API_KEY` など必要な値を設定。
   ```bash
   cp .env.sample .env
   ```
2. 依存関係は `make install` でまとめて導入（backend=uv、frontend=npm）。個別に行う場合は `uv sync` と `npm install` を直接実行。
   ```bash
   make install
   # or
   (cd backend && uv sync)
   (cd frontend && npm install)
   ```
3. `backend/.venv` は `make` 内で自動生成されるため、通常は手動操作不要。

## 実行・デバッグ手順

### バックエンド単体
```bash
cd backend
uv sync  # 初回のみ
MODE=fake DB_MODE=sqlite uv run scripts/seed.py  # 03 以降で必要な場合
uv run uvicorn uvicorn_app:app --reload --host 0.0.0.0 --port 8089
```
- `MODE=fake` なら OpenAI API Key なしでスタブデータを返す。`MODE=live` で実 API を利用する際は `.env` にキーを記載。
- ポート変更時は `BACKEND_PORT` 環境変数と `--port` を揃える。

### フロントエンド単体
```bash
cd frontend
npm install  # 初回のみ
VITE_API_BASE=http://localhost:8089 npm run dev -- --host 0.0.0.0 --port 5173
```
- `VITE_API_BASE` はバックエンド URL と一致させる。Codespaces では `https://<forwarded-host>-8089.app.github.dev` 形式を設定。

### Makefile で同時起動
```bash
MODE=fake DB_MODE=sqlite BACKEND_PORT=8089 FRONTEND_PORT=5173 make dev
```
- `make backend` / `make frontend` で片方のみ、`make seed` でベクトルストア生成、`make clean` で主要生成物を削除。
- プランニング API は `/api/plan`。`MODE=fake` ではテンプレート応答、`MODE=live` で OpenAI (gpt-4o-mini 既定) を用いた LangGraph 実行に切り替わり、フロントの「面談用プランボード」に反映される。

## 環境変数と設定メモ

- `MODE`: `fake` または `live`。推論エンジンやシード時の Embeddings を切り替え。
- `DB_MODE`: `sqlite`（既定）か `json`。JSON 利用時は `JSON_DB_DIR` で格納先を指定。
- `BACKEND_PORT` / `FRONTEND_PORT`: 既定 8089 / 5173。`VITE_API_BASE` も合わせて更新。
- `ALLOWED_ORIGINS`: FastAPI の CORS 設定。ローカル用途では `["*"]`。本番用途では URL 配列を文字列で渡す。
- `.env` はコミット禁止。新規キーを追加したら PR の説明に記載し、秘密は共有ツール経由で受け渡す。

## テストと検証

- バックエンド: `make test`（内部で `PYTHONPATH=app pytest -q`）。新規ルートは `backend/app/tests/test_<feature>.py` を追加し、ステータス・レスポンスを検証。
- LangGraph プランナーは `backend/app/tests/test_plan.py` で API レベルのスナップショットを確認。Fake モードで deterministic に通るように保つ。
- フロントエンド: `npm run lint` を実行。必要に応じて `frontend/src/__tests__/` に Vitest/Playwright を追加し、対応 npm スクリプトを整備。
- シード後は `backend/data/vectorstore` の更新有無と `readlink` などでデータ/リンクの整合性を確認。
- 複数ステップを切り替える場合は、対象ディレクトリの `.env`・`backend/data` が期待どおりに存在するかを都度確認。

## GitHub Codespaces 利用時の注意

- まず `uv` をインストールし、`cp .env.sample .env` でキーを設定する。
- `backend` を先に起動して `http://0.0.0.0:8089` に出る案内から公開 URL を取得し、ポート 8089 を Public に変更。
- `frontend` 起動時の `VITE_API_BASE` に公開 URL を設定し、ポート 5173 にアクセス。
- Codespaces 以外でも、リモート環境では `--host 0.0.0.0` を忘れず指定。
