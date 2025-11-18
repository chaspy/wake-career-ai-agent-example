# 02_profile_api

前フェーズとの違い: ヘルスチェックのみだった 01 から、プロフィール保存/取得を追加。LLM は使いません。

## できること
- `/api/health` でフェーズ確認
- `/api/profile` GET/PUT でプロフィールをローカル `profile.json` に保存
- フロントでフォーム入力→保存→再読込で値が残る

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

ポート競合時は `BACKEND_PORT` / `FRONTEND_PORT` を適宜変更してください。
