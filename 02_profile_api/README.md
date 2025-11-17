# 02_profile_api

前フェーズとの違い: ヘルスチェックのみだった 01 から、プロフィール保存/取得を追加。LLM は使いません。

## できること
- `/api/health` でフェーズ確認
- `/api/profile` GET/PUT でプロフィールをローカル `profile.json` に保存
- フロントでフォーム入力→保存→再読込で値が残る

## 動かし方
```bash
cd 02_profile_api
make dev
# http://localhost:5173 を開きフォームで保存
```
