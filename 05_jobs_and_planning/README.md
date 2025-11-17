# WAKE Career AI Agent (WIP)

ローカルで Vite/React フロントと FastAPI バックエンドを並列起動できる最小スキャフォールドです。Step 1 ではプロフィール API と SQLite/JSON の永続化を追加しました。今後のステップで RAG 推薦機能や LangGraph を実装していきます。

## 必須ツール

- [uv](https://github.com/astral-sh/uv) （Python 依存の解決と仮想環境作成に利用）
- Node.js 20 以上 / npm 10 以上
- make

## ハンズオン参加者向け 事前準備チェックリスト（15–20分）

1. Git と Node.js をインストール
   - Git: https://git-scm.com/downloads
   - Node.js: v20 以上（https://nodejs.org/）
   - 動作確認: `git --version` / `node -v` / `npm -v`

2. Python と uv を準備
   - Python 3.11 以上を用意（3.12 でも可）
   - uv インストール: `curl -LsSf https://astral.sh/uv/install.sh | sh`
   - 確認: `uv --version`

3. リポジトリ取得
   ```bash
   git clone https://github.com/chaspy/wake-career-ai-agent-example.git
   cd wake-career-ai-agent-example
   ```

4. 環境ファイルを用意
   ```bash
   cp .env.sample .env
   # .env を開き、OPENAI_API_KEY=sk-... を記入（キーが無い場合は空でOK）
   # MODE は live のままで可。キー未設定なら自動で fake モードになります。
   ```

5. 依存インストール
   ```bash
   make install
   ```
   - backend の仮想環境（`backend/.venv`）と frontend の npm 依存をまとめて導入します。

6. 動作確認（余裕があれば）
   ```bash
   MODE=fake make dev
   # ブラウザで http://localhost:5173 を開き、Health が "fake" で OK 表示になることを確認
   # Ctrl+C で終了
   ```

当日: `make dev` を実行し、ブラウザで http://localhost:5173 を開くだけで体験できます。OpenAI キーありの参加者は `.env` にキーを入れて live 推論、無い参加者は fake モードで UI 体験が可能です。

## 現状の開発フロー (Step 0)

```bash
cp .env.sample .env  # 任意。未作成でも MODE=fake で起動
make install         # backend と frontend の依存を導入
MODE=fake make dev   # :8089 (API) / :5173 (Vite) を同時起動
```

`make install` では uv が `backend/.venv` を生成し、`requirements.txt` を同環境にインストールします。uv が PATH に無い場合は先に `curl -LsSf https://astral.sh/uv/install.sh | sh` などで導入してください。

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
   python backend/scripts/fetch_wake_article.py \
     --url https://wake-career.jp/articles/awesome \
     --tags "キャリア,AI" \
     --category ai-career
   ```
   `backend/data/wake_articles/` に front matter 付き Markdown が生成されます。
2. `make seed` または `python backend/scripts/seed.py` を実行すると、記事が分割・ベクトル化され `backend/data/vectorstore/` に保存されます。同時に ArticleIndex (SQLite/JSON) が更新されます。

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
