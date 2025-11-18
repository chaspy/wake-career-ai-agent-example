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

## 起動手順（最短）
```bash
cd 01_bootstrap
make dev   # 初回は内部で uv run / npm install が走ります
```

依存を先に入れて高速起動したい場合:
```bash
cd 01_bootstrap/backend && uv sync && cd ..
cd frontend && npm install && cd ..
make dev
```
ポート変更は `BACKEND_PORT` / `FRONTEND_PORT` を上書きしてください（デフォルト 18089 / 15073）。
