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

### LangChain を使う箇所（抜粋）
- `backend/app/main.py` の `/api/ping-llm` で ChatOpenAI を直呼びしています。API キーが無いときはダミー応答を返すフェイルセーフ付き。

```python
# backend/app/main.py
llm = ChatOpenAI(model=model, api_key=api_key, temperature=0)
out = llm.invoke([{"role": "user", "content": payload.prompt}])
return PingResponse(reply=str(out.content), mode="live")
```


## 起動手順

### 推奨: backend / frontend を個別に起動

1. バックエンド（FastAPI）
   ```bash
   cd 01_bootstrap/backend
   uv sync
   uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 18089
   ```
   - OpenAI を実際に叩きたい場合は、上記を実行するシェルで `export OPENAI_API_KEY=...` を設定してください。未設定でも fake 応答で動作します。

2. フロントエンド（Vite）
   ```bash
   cd 01_bootstrap/frontend
   npm install
   npm run dev -- --host 0.0.0.0 --port 15073
   ```
   - `vite.config.ts` が `/api` を `http://localhost:18089` にプロキシするため、追加の環境変数設定は不要です。

3. ブラウザで http://localhost:15073 を開き、ヘルスチェックと LLM 疎通を確認。

### make が使える場合

```bash
cd 01_bootstrap
make dev   # backend 18089 / frontend 15073 を同時起動
```

`BACKEND_PORT` と `FRONTEND_PORT` を上書きするとポートを変えられます（例: `BACKEND_PORT=19000 FRONTEND_PORT=16000 make dev`）。
