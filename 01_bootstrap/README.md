# 01_bootstrap

FastAPI + Vite の最小スキャフォールド。健康チェックと LLM 疎通用のエンドポイントだけを持つ「素の状態」です。

## このステップでできること
- `/api/health` … サーバが生きているかの確認
- `/api/ping-llm` … LLM キーがあれば実呼び出し、無ければダミー応答（mode=fake）

## 前ステップとの差分
- ステップ0は存在せず、このリポの出発点。以降のステップはここに機能を積み上げていきます。

## 仕組み（ざっくり）
- backend: `app/main.py` だけのシンプル構成。`ChatOpenAI` をキー有無で切り替え。
- frontend: ほぼ静的。ヘルスと ping の結果を表示する最小 UI。

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

ポートを変えたい場合は `BACKEND_PORT` / `FRONTEND_PORT` を上書きして実行してください。
