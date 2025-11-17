# 03_articles_ingest

前フェーズとの差分: プロフィールに加え、記事の ingest/一覧/詳細を追加（RAGなし）。
- `/api/articles` で Markdown 記事の一覧
- `/api/articles/{slug}` で本文取得
- サンプル記事は `backend/app/data/articles/sample.md`

## 動かし方
```bash
cd 03_articles_ingest
make dev
# ブラウザで記事一覧から選択→詳細表示
```
