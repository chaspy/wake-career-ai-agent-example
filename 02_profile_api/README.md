# 02_profile_api

ヘルスチェックだけだった 01 に「プロフィールの保存/取得」を追加し、保存済みプロフィールを LLM に渡して簡易アドバイスを返せるようにしました（OpenAI キーなしでもフェイク応答で動作）。

## 前ステップとの違い
- 追加: `/api/profile` GET/PUT。プロフィールをファイル永続化（デフォルト JSON、後続ステップで DB 切替を導入）。
- health 応答を本番仕様に寄せ、フェーズ名を返します。

## 01_bootstrap との実装差分（丁寧解説）
- **LLM 呼び出しの位置づけ変更**: `/api/ping-llm` の単発プロンプト送信を削除し、プロフィールを踏まえた `/api/profile/advice` に置き換え。LLM へ渡す情報が「自由文」→「保存済みプロフィール + 質問」に進化。
- **永続化の導入**: 01 はステートレスだったが、02 は `backend/app/profile.json` へ JSON 保存。未存在時はサンプル `WAKE Guest` を自動生成して UX を途切れさせない。
- **依存ライブラリ**: 01 は `langchain_openai.ChatOpenAI` 経由だったが、02 は `openai` SDK の生チャット API に変更。キー未設定時はフェイク応答を返し、デバッグしやすくしている。
- **health 応答**: `{"ok": true}` から `{"ok": true, "phase": "02_profile_api"}` に拡張し、フロントでフェーズ表示・疎通確認をしやすくした。
- **フロント UI**: LLM ping フォームは撤去し、プロフィール編集フォーム＋「LLM にキャリア相談」セクションに差し替え。保存値を自動ロード/反映し、回答プロバイダー（openai/fake）も表示。
- **スタイルの微調整**: `.shell` ラッパで横幅を `min(760px, 92vw)` にし、モバイルでも左右に余白を確保。カード/パネル構成は 01 のトーンを踏襲しつつ改修。

### コードレベルの差分（ファイル別に一つずつ）
- `backend/app/main.py`
  - `/api/ping-llm` を削除し、`/api/profile` GET/PUT で JSON 永続化（64-66 行付近）。未保存時は `DEFAULT_PROFILE` を自動生成（33-42 行）。
  - 新規 `/api/profile/advice` エンドポイント（119-130 行）。プロフィールをプロンプト化する `_build_prompt`、OpenAI 呼び出し `_call_openai`、キー未設定時のフェイク応答 `_fake_answer` を追加。
  - 依存を `openai` SDK に変更し、LangChain への依存を排除。
- `backend/pyproject.toml` / `backend/requirements.txt` / `backend/uv.lock`
  - 依存に `openai` を追加しロックを更新。01 では `langchain_openai` があり、02 では不要。
- `frontend/src/main.tsx`
  - 01 の「LLM に送る」フォームを撤去し、プロフィール入力フォームと保存・再読み込み、アドバイス取得ボタンを実装。
  - `askAdvice` 関数で `/api/profile/advice` を呼び、provider 表示と回答を `<pre>` に描画する処理を追加（144-173 行）。
- `frontend/src/style.css`
  - `.shell` レイアウトを新設し、左右マージンと最大幅を指定。01 の `.app-shell` 相当は使わず、02 用に薄く調整。
- `README.md`
  - 上記機能説明と差分解説を追加（本節）。01 では README に LLM 疎通のみを記載していたが、02 ではプロフィール保存・アドバイス取得・OpenAI キー設定方法まで網羅。

## できること（API）
- `/api/health` … フェーズ確認
- `/api/profile` … プロフィール保存/取得（JSON ファイル直書き）
- `/api/profile/advice` … 保存済みプロフィールをプロンプトに埋め込み、LLM からキャリアアドバイスを取得（`OPENAI_API_KEY` 未設定時はフェイク生成）
  - プロフィール未設定でも初回アクセス時にサンプル（WAKE Guest）を自動生成するので、そのまま試せます。

## コードの見どころ
- backend: `app/main.py` で Pydantic モデルを定義し、ローカル JSON (`profile.json`) へ読み書き。
- 将来の DB 切替に備え、I/O を関数で分離しているので Step03 以降に差し替えやすい構造。
- frontend: フォーム入力→保存→再読込で値が残るシンプル UI。

## 起動手順（最短）
```bash
cd 02_profile_api
make dev   # 初回は内部で uv run / npm install が走ります
```

高速化したい場合（依存を事前導入）
```bash
cd 02_profile_api/backend && uv sync && cd ..
cd frontend && npm install && cd ..
make dev
```
デフォルトポートは backend 28089 / frontend 25073。競合する場合は `BACKEND_PORT` / `FRONTEND_PORT` を上書きしてください。

### OpenAI を使う場合
環境変数に API キーをセットしてください（モデルは `OPENAI_MODEL` で上書き可、デフォルト `gpt-4o-mini`）。
```bash
export OPENAI_API_KEY=sk-xxxxx
export OPENAI_MODEL=gpt-4o-mini  # 省略可
```
