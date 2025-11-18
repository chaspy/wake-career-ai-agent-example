# 02_profile_api

ヘルスチェックだけだった 01 に「プロフィールの保存/取得」を追加し、保存済みプロフィールを LLM に渡して簡易アドバイスを返せるようにしました（OpenAI キーなしでもフェイク応答で動作）。

## 前ステップとの違い
- 追加: `/api/profile` GET/PUT。プロフィールをファイル永続化（デフォルト JSON、後続ステップで DB 切替を導入）。
- health 応答を本番仕様に寄せ、フェーズ名を返します。

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
