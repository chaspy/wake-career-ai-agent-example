# 02_profile_api

ヘルスチェックだけだった 01 に「プロフィールの保存/取得」を追加。LLM 依存なしで動きます。

## 前ステップとの違い
- 追加: `/api/profile` GET/PUT。プロフィールをファイル永続化（デフォルト JSON、後続ステップで DB 切替を導入）。
- health 応答を本番仕様に寄せ、フェーズ名を返します。

## できること（API）
- `/api/health` … フェーズ確認
- `/api/profile` … プロフィール保存/取得（JSON ファイル直書き）

## コードの見どころ
- backend: `app/main.py` で Pydantic モデルを定義し、ローカル JSON (`profile.json`) へ読み書き。
- 将来の DB 切替に備え、I/O を関数で分離しているので Step03 以降に差し替えやすい構造。
- frontend: フォーム入力→保存→再読込で値が残るシンプル UI。

## 起動手順（uv sync 統一）
```bash
cd 02_profile_api

# backend 依存（uv sync が .venv を自動作成）
cd backend && uv sync && cd ..

# frontend 依存
cd frontend && npm install && cd ..

# 開発サーバ起動（デフォルト: backend 28089 / frontend 25073）
BACKEND_PORT=28089 FRONTEND_PORT=25073 make dev
# ブラウザ: http://localhost:25073
```

ポート競合時は `BACKEND_PORT` / `FRONTEND_PORT` を上書きしてください。
