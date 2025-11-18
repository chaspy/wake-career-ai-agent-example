# WAKE Career AI Agent

このリポジトリは 2025/11/18 開催の [ハンズオン】1 時間で作る自作 AI エージェント〜LangChain × LangGraph〜](https://wake-career.connpass.com/event/372312/) で利用するサンプルリポジトリです。

## 免責事項

- 本リポジトリはあくまで手を動かして AI Agent を体験するための手がかりとなるサンプルコードであり、動作や品質を保証しません
- 本リポジトリの内容は予告なく変更されることがあります

## サンプルアプリケーションについて

ローカルで Vite/React フロントと FastAPI バックエンドを並列起動できる最小スキャフォールドです。ステップを追うごとに「プロフィール → 記事/RAG → 求人 → プランニング」と機能が増えていきます。

- `01_bootstrap` → `02_profile_api` → `03_articles_ingest` → `04_recommend_rag` → `05_jobs_and_planning`（＝ルートと同等）の順に機能が積み上がります。
- 各フォルダは「その時点の完成形」を丸ごと持つスナップショットです。**混ぜずに、動かしたいステップを単体で起動**してください。
- 最新機能を一気に見たい人はリポジトリ直下（`backend/`, `frontend/`）を使えば OK です。
- 01_bootstrap からはじめて、少しずつ実装を進めるのも良いでしょう。ディレクトリを切り替えて、動作確認しながら、コードの diff を見るのも良いでしょう。
- もちろんあなただけのオリジナルの AI Agent を作るのも構いません

## Setup

## QuickStart

git, node, python, uv がある場合、以下で動作確認ができます。

```bash
git clone https://github.com/chaspy/wake-career-ai-agent-example.git
cd wake-career-ai-agent-example
cp .env.sample .env # Set OPENAI_API_KEY
make dev   # backend:8089 / frontend:5173
```

ブラウザで http://localhost:5173 を開いてください。

## Installation（ツール導入を丁寧に）

- Git: macOS は多くの環境で標準。無ければ `xcode-select --install` または https://git-scm.com/downloads からインストール。
  - 確認: `git --version`
- Python 3.11 以上:
  - macOS (Homebrew): `brew install python@3.12`
  - Windows: https://www.python.org/downloads/ で 3.11+ を入れ、「Add Python to PATH」をオン。
  - 確認: `python3 --version`
- uv: Python の依存解決と仮想環境作成をまとめて行うツール。
  - インストール: `curl -LsSf https://astral.sh/uv/install.sh | sh`（macOS/Linux）
  - PowerShell: `irm https://astral.sh/uv/install.ps1 | iex`
  - 確認: `uv --version`
- Node.js 20 以上 / npm 10 以上:
  - macOS (Homebrew): `brew install node@20`
  - 公式: https://nodejs.org/ から LTS (20+) を取得
  - 確認: `node -v` / `npm -v`
- make:
  - macOS: 標準。無ければ `xcode-select --install`
  - Windows: WSL や Git Bash で利用するか `choco install make`
  - 確認: `make -v`

インストールが終われば Quick Start の手順で動作確認してください。

## Trouble Shooting

- `uv: command not found` → uv を入れてから `uv sync` を実行。
- `Failed to spawn: uvicorn` → 依存未インストール。`cd backend && uv sync` を先に。
- ポート競合 (5173/8089 使用中) → `BACKEND_PORT=9000 FRONTEND_PORT=5200 MODE=fake make dev` などで上書き。
- RAG が 503 → seed 未実行。RAG があるステップで `cd backend && uv run python scripts/seed.py`。

### フェーズ別の起動ポート

- 01_bootstrap: backend 18089 / frontend 15073
- 02_profile_api: backend 28089 / frontend 25073
- 03_articles_ingest: backend 38089 / frontend 35073
- 04_recommend_rag: backend 48089 / frontend 45073
- 05_jobs_and_planning: backend 8089 / frontend 5173（完成版）

※ それぞれ `make dev` で立ち上がります。複数フェーズを同時に起動する場合もポート衝突しません。

### 各フェーズ共通の起動手順（uv sync 統一）

以下のコマンドブロックを、対象フェーズのディレクトリ名とポートに置き換えて実行してください。

```bash
cd 02_profile_api

make dev
# ブラウザ: http://localhost:25073
```
