# WAKE Career AI Agent (WIP)

ローカルで Vite/React フロントと FastAPI バックエンドを並列起動できる最小スキャフォールドです。ステップを追うごとに機能が増え、最終的に「プロフィール + 記事/RAG + 求人 + プランニング」がそろいます。

## だれ向けのガイドか
- **初心者エンジニア / 学習者**: 手順をそのままコピペすれば動くよう、理由付きで並べています。
- **ビジネス職・非エンジニア**: 「最低限これだけ」で動く 3 コマンドを先に示し、その後に詳しい説明を分けています。開発者がそばにいなくても読み進められるようにしました。

## フェーズはスナップショット方式
- `01_bootstrap` → `02_profile_api` → `03_articles_ingest` → `04_recommend_rag` → `05_jobs_and_planning`（＝ルートと同等）の順に機能が積み上がります。
- 各フォルダは「その時点の完成形」を丸ごと持つスナップショットです。**混ぜずに、動かしたいステップを単体で起動**してください。
- 最新機能を一気に見たい人はリポジトリ直下（`backend/`, `frontend/`）を使えば OK です。

## 最短 3 コマンド（前提: Git・Node・Python・uv 済み）
```bash
git clone https://github.com/chaspy/wake-career-ai-agent-example.git
cd wake-career-ai-agent-example
MODE=fake make dev   # backend:8089 / frontend:5173
```
ブラウザで http://localhost:5173 を開けば UI が動きます。OpenAI キーが無い場合でも fake モードで最後まで体験できます。

## 必須ツール

- [uv](https://github.com/astral-sh/uv) （Python 依存の解決と仮想環境作成に利用）
- Node.js 20 以上 / npm 10 以上
- make

## じっくり準備する手順（初心者・ビジネス職向けに丁寧め）
1. **ツール確認**（約3分）
   - `git --version` / `node -v` / `npm -v` / `python3 --version` / `uv --version`
   - どれか無ければインストール（リンク: Git / Node.js v20+ / Python3.11+ / `curl -LsSf https://astral.sh/uv/install.sh | sh`）。

2. **リポジトリを取得**（約1分）
   ```bash
   git clone https://github.com/chaspy/wake-career-ai-agent-example.git
   cd wake-career-ai-agent-example
   ```

3. **環境ファイルを用意**（約1分）
   ```bash
   cp .env.sample .env
   # OpenAI キーがあれば OPENAI_API_KEY=sk-... を記入。無ければ空欄でOK（自動で fake モード）。
   ```

4. **依存インストール**（約3〜5分）
   ```bash
   cd backend && uv sync && cd ..
   cd frontend && npm install && cd ..
   ```
   - ここで Python 仮想環境が `backend/.venv` に作られます。

5. **起動**（約1分）
   ```bash
   MODE=fake make dev
   ```
   - ブラウザで http://localhost:5173 を開く。
   - 画面左上の Health が `fake` と表示されれば成功。live にしたいときは `.env` にキーを入れて再起動。

6. **止め方**
   - ターミナルで `Ctrl+C` を押すだけ（バックエンド・フロントエンド両方が止まります）。

### トラブルシュート早見表
- `uv: command not found` → uv をインストールしてから再度 `uv sync`。
- `Failed to spawn: uvicorn` → 依存未インストール。`cd backend && uv sync` を先に。
- ポート競合（すでに 5173/8089 が使用中）→ `BACKEND_PORT=9000 FRONTEND_PORT=5200 MODE=fake make dev` のように上書き。
- RAG が 503 を返す → seed 未実行。該当ステップ（03/04/ルート）で `cd backend && uv run python scripts/seed.py`。

## フェーズ別の起動ポート
- 01_bootstrap: backend 18089 / frontend 15073
- 02_profile_api: backend 28089 / frontend 25073
- 03_articles_ingest: backend 38089 / frontend 35073
- 04_recommend_rag: backend 48089 / frontend 45073
- 05_jobs_and_planning: backend 8089 / frontend 5173（完成版）

※ それぞれ `make dev` で立ち上がります。複数フェーズを同時に起動する場合もポート衝突しません。

## 各フェーズ共通の起動手順（uv sync 統一）
以下のコマンドブロックを、対象フェーズのディレクトリ名とポートに置き換えて実行してください。

```bash
# 例: 02_profile_api を backend 28089 / frontend 25073 で起動する場合
cd 02_profile_api

# backend 依存（uv sync が .venv を自動作成）
cd backend && uv sync && cd ..

# frontend 依存
cd frontend && npm install && cd ..

# 開発サーバ起動（ポートは上の表から対応する値をセット）
BACKEND_PORT=28089 FRONTEND_PORT=25073 make dev
# ブラウザ: http://localhost:25073
```

`BACKEND_PORT` / `FRONTEND_PORT` は上の表の値を使うか、都合にあわせて変更してください。uv が無い場合は `curl -LsSf https://astral.sh/uv/install.sh | sh` で導入できます。

## 現状の開発フロー (Step 0)

```bash
cp .env.sample .env  # 任意。未作成でも MODE=fake で起動
make install         # backend と frontend の依存を導入
MODE=fake make dev   # :8089 (API) / :5173 (Vite) を同時起動
```

`uv sync` は `.venv` を自動生成し、`requirements.txt` に基づいて依存をインストールします。uv が PATH に無い場合は先に `curl -LsSf https://astral.sh/uv/install.sh | sh` などで導入してください。

Makefile はリポジトリ直下の `.env` を自動で読み込み、`MODE` や `DB_MODE`、ポート番号などをそのままコマンドへエクスポートします。値を変えたい場合は `.env` を編集するだけで `make dev` などのターゲットに反映されます。

ブラウザで `http://localhost:5173` を開き、Health API の応答が表示されれば準備完了です。`MODE` のデフォルトは `live` ですが、OpenAI API キーが未設定の場合は自動的に `fake` モードとして動作します。API の待受ポートは `.env` の `BACKEND_PORT`（デフォルト 8089）で調整できます。

## プロフィール API (Step 1)

```bash
# SQLite を利用する例
MODE=fake DB_MODE=sqlite curl -s http://localhost:8089/api/profile # => 404 (未設定)

curl -X PUT http://localhost:8089/api/profile \
  -H 'Content-Type: application/json' \
  -d '{
        "name":"Alice",
        "years":5,
        "current_role":"Frontend Engineer",
        "target_role":"AI Product Manager",
        "skills":["React","Python"],
        "interests":["Career Coaching"],
        "notes":"Looking for AI-assisted workflows"
      }'

curl -s http://localhost:8089/api/profile | jq

# JSON モード
DB_MODE=json JSON_DB_DIR=/tmp/wake-json MODE=fake BACKEND_PORT=9000 uvicorn uvicorn_app:app --reload --port 9000
```

`DB_MODE=json` に切り替えると `backend/data/db/profile.json`（もしくは `JSON_DB_DIR` で指定したパス）に保存されます。

## 記事取り込み & ベクトル化 (Step 2)

1. WAKE Career の許諾済み記事を Markdown 化します。
   ```bash
   cd backend && uv run python scripts/fetch_wake_article.py \
     --url https://wake-career.jp/articles/awesome \
     --tags "キャリア,AI" \
     --category ai-career
   ```
   `backend/data/wake_articles/` に front matter 付き Markdown が生成されます。
2. `make seed` または `cd backend && uv run python scripts/seed.py` を実行すると、記事が分割・ベクトル化され `backend/data/vectorstore/` に保存されます。同時に ArticleIndex (SQLite/JSON) が更新されます。

```bash
MODE=fake DB_MODE=sqlite make seed
# => [seed] 2 件の記事を faiss で保存しました。path=backend/data/vectorstore/faiss ...
```

`.sample.md` で終わるファイルはダミーデータとしてコミット済みです。本番では `.md` を配置し、`tags` / `category` / `published` を front matter に記述してください。

## 推薦 API (Step 3)

FAISS/Chroma に記事が登録済みであれば、FastAPI の `/api/recommendations` から RAG 推薦を取得できます。

```bash
MODE=fake DB_MODE=sqlite BACKEND_PORT=8089 uvicorn uvicorn_app:app --reload --port 8089 &

curl -s -X POST http://localhost:8089/api/recommendations \
  -H 'Content-Type: application/json' \
  -d '{
        "query": "AI PM キャリア",
        "top_k": 2
      }' | jq
```

レスポンス例:

```json
{
  "mode": "fake",
  "recommendations": [
    {
      "title": "WAKE Career 実践AI PM",
      "reasons": ["target role..."],
      "citations": [
        {
          "source_url": "https://wake-career.jp/media/wakeskill-1on1",
          "title": "WAKE Career 実践AI PM",
          "line": 5
        }
      ]
    }
  ]
}
```

MODE=live かつ `OPENAI_API_KEY` を設定すると、LangGraph の call_model ノードが ChatOpenAI を用いて理由文を生成します（引用スラッグ必須のプロンプトでJSONを出力）。キーが無い場合でも fake モードで最後まで同じスキーマのレスポンスが得られます。
