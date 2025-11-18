# 04_recommend_rag

前フェーズとの差分: RAG に加えて求人検索を追加。ここで「おすすめ記事 + 求人」の双方向を見るステップ。
- `/api/articles`・`/api/articles/{slug}` … 03 と同じ
- `/api/recommendations` … FAISS 検索＋ fake/live 理由生成
- `/api/jobs/search` … 求人フェイク検索（キーワード・ロケーション）

## 起動手順（最短）
```bash
cd 04_recommend_rag
make dev   # 初回は内部で uv run / npm install が走ります

# RAG 用ベクトルストアを作る（初回だけでOK）
cd backend && uv sync && uv run python scripts/seed.py && cd ..
cd frontend && npm install && cd ..
make dev
# ブラウザ: http://localhost:45073 （記事一覧・RAG・求人の3カラム表示）

## 仕組みの要点
- 記事/RAG 部分は Step03 と同じ（FAISS ロード＋類似検索）。
- 求人は fake 実装（サンプル3件をクエリ・ロケーションに合わせて返却）。live 化したい場合は `jobs` ロジックを差し替えれば踏み台になります。
- health が `mode`/`provider` を返すので、fake か live か UI から判別可能。

## フロントの流れ
1. 左: 記事リスト → 詳細。
2. 中: RAG クエリ入力 → 推薦カード（score / 抜粋 / 理由）。
3. 右: 求人キーワード入力 → fake ジョブカード（会社・ロケーション・説明）。
```

「おすすめを取得（ダミー）」でカード表示されれば準備完了。ポート競合時は環境変数で変更してください。
