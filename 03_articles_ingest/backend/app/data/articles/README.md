# WAKE 記事スナップショットの配置方法

1. `python backend/scripts/fetch_wake_article.py --url <WAKE記事URL>` を実行すると、フロントマター付き Markdown が `backend/data/wake_articles/` に作成されます。
2. 自前で Markdown を用意する場合は、以下の front matter を必ず付与してください。

```yaml
---
title: 無限に学べるWAKE記事
source_url: https://wake-career.jp/articles/awesome
published: 2024-06-12
tags:
  - キャリア
  - スキルアップ
category: product-career
---
```

本文は Markdown 形式で、H1/H2 の見出しやリストを自由に記述できます。`make seed`（または `python backend/scripts/seed.py`）を実行すると、これらの記事がベクトル化され `backend/data/vectorstore/` に保存されます。

> `.sample.md` 拡張子のファイルはリポジトリにコミットしてもよいテスト用のダミー記事です。実際の WAKE 記事は `.md` で保存してください（`.gitignore` により無視されます）。
