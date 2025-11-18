# AI Agent クイックスタート

- 返答は常に日本語（コードやログは英語のままで可）。
- `.codex/prompts/` や `.claude/commands/` にある既存スラッシュコマンドを優先して再利用。
- 判断に迷ったら必ずユーザに確認。独断で決めない。
- `git` / `gh` を積極活用して作業内容を管理。
- 作業前に本ファイルと `README.md` を確認すると最短で全体像を掴める。

## リポジトリ概要（WAKE Career AI Agent Example）

### ディレクトリ構成
- `backend/`: FastAPI サービス。主要コードは `backend/app`（routers、`rag/` の LangChain 補助、設定、DB ヘルパ）。
- `backend/data/`: wake 記事 markdown、FAISS/Chroma ベクタストア、SQLite/JSON のプロフィールスナップショットを保持。インジェスト系スクリプトは `backend/scripts/`。
- `frontend/`: Vite + React クライアント。コードは `frontend/src`、静的アセットは `public/`。
- テストは `backend/app/tests` に配置（health、profile、ingest、recommend など API ごと）。

### 開発・実行コマンド
- `cp .env.sample .env`: 開発用の環境変数を用意。
- `make install`: バックエンド依存とフロントエンドの `npm install` をまとめて実行。
- `MODE=fake make dev`: uvicorn(`:8089`) と Vite(`:5173`) を同時起動（協調シャットダウン）。
- `make backend` / `make frontend`: 片方だけ起動。ポートや DB モードは環境変数で上書き可。
- `MODE=fake DB_MODE=sqlite make seed`: `backend/data/wake_articles` の markdown から FAISS/Chroma チャンクを生成。
- `make test`: pytest を実行。フロントエンドの本番ビルドは `cd frontend && npm run build`。

### コーディング規約
Python: 4 スペースインデント。FastAPI エンドポイントには型ヒントと Pydantic のリクエスト/レスポンスモデルを使用。router は薄く保ち、ビジネスロジックは `db.py`・`rag/`・専用ヘルパへ。関数/モジュールは snake_case、クラスは PascalCase。
Frontend: strict TypeScript・関数コンポーネント。ファイル名は PascalCase（例: `ProfilePanel.tsx`）、フック/ステートは camelCase。コミット前に `npm run lint`。

### テスト指針
- プッシュ前に `make test`（`PYTHONPATH=app` が自動設定）。
- 新規ルートは `backend/app/tests/test_<feature>.py` を追加し、ステータスとペイロード両方を検証。
- `backend/data` のサンプルが不足する場合は刷新してからテスト。
- フロントエンドは手動テストが基本。Vitest/Playwright を追加する場合は `frontend/src/__tests__/` に置き、対応 npm スクリプトを記載。

### コミット / PR ルール
- Conventional Commits（`feat:`, `fix:`, `chore:` など）を踏襲。1 コミット 1 関心（コード + テスト + データ更新）。
- PR には変更概要、環境やデータ変更点（例: `make seed` 要再実行、`.env` 追加キー）、挙動変化時のスクショや `curl` 例、WAKE Career のトラッキング課題リンクを含める。

### 環境・設定メモ
- `MODE` でフェイク/本番推論を切替（本番は `OPENAI_API_KEY` 必須）。
- プロフィール永続化は `DB_MODE=sqlite`（標準）または `json`。JSON は `JSON_DB_DIR` でパス変更可。
- `BACKEND_PORT` / `FRONTEND_PORT` を調整し、`VITE_API_BASE` と合わせる。
- `.env` はコミット禁止。新しいキーは PR で言及し、秘密はマネージャ経由で共有。
