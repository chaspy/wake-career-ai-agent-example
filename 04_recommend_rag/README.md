# 04_recommend_rag

前フェーズとの差分: 簡易推薦エンドポイントを追加（LLMなしの fake RAG）。求人・プランニングはまだ無し。
- `/api/recommendations` は先頭記事をダミー推薦として返す
- 記事一覧/詳細は 03 と同じ

## 動かし方
```bash
cd 04_recommend_rag
make dev
# 「おすすめを取得（ダミー）」で理由付きカードが出ればOK
```
