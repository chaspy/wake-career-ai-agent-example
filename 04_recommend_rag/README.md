# 04_recommend_rag

前フェーズとの差分: 簡易推薦エンドポイントを追加（LLMなしの fake RAG）。求人・プランニングはまだ無し。
- `/api/recommendations` は先頭記事をダミー推薦として返す
- 記事一覧/詳細は 03 と同じ

## 起動手順（uv sync 統一）
```bash
cd 04_recommend_rag

# backend 依存（uv sync が .venv を自動作成）
cd backend && uv sync && cd ..

# frontend 依存
cd frontend && npm install && cd ..

# 開発サーバ起動（デフォルト: backend 48089 / frontend 45073）
BACKEND_PORT=48089 FRONTEND_PORT=45073 make dev
# ブラウザ: http://localhost:45073
```

「おすすめを取得（ダミー）」でカード表示されれば準備完了。ポート競合時は環境変数で変更してください。
