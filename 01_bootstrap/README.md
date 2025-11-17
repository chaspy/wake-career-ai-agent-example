# 01_bootstrap

最小構成でフロントと FastAPI を同時起動し、`/api/health` が返ることだけを確認するフェーズです。

- 目的: 開発環境が起動することを最速で確認する
- 使い方:
  ```bash
  make dev   # ルートの Makefile を使用
  # http://localhost:5173 で Health が表示されればOK
  ```
