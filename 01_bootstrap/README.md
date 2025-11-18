# 01_bootstrap

基本のフロント/バックエンド同時起動フェーズ。セットアップは uv に統一しています。

## 起動手順（uv sync 統一）
```bash
cd 01_bootstrap

# backend 依存（uv sync が .venv を自動作成）
cd backend && uv sync && cd ..

# frontend 依存
cd frontend && npm install && cd ..

# 開発サーバ起動（デフォルト: backend 18089 / frontend 15073）
BACKEND_PORT=18089 FRONTEND_PORT=15073 make dev
# ブラウザ: http://localhost:15073
```

ポートを変えたい場合は上記の `BACKEND_PORT` / `FRONTEND_PORT` を任意に指定してください。
