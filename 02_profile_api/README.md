# 02_profile_api

ヘルスチェックだけだった 01 に「プロフィールの保存/取得」を追加し、保存済みプロフィールを LLM に渡して簡易アドバイスを返せるようにしました（OpenAI キーなしでもフェイク応答で動作）。

## 前ステップとの違い
- 追加: `/api/profile` GET/PUT。プロフィールをファイル永続化（デフォルト JSON、後続ステップで DB 切替を導入）。
- health 応答を本番仕様に寄せ、フェーズ名を返します。

## 01_bootstrap との実装差分（丁寧解説）
- **LLM 呼び出しの位置づけ変更**: `/api/ping-llm` の単発プロンプト送信を削除し、プロフィールを踏まえた `/api/profile/advice` に置き換え。LLM へ渡す情報が「自由文」→「保存済みプロフィール + 質問」に進化。
- **永続化の導入**: 01 はステートレスだったが、02 は `backend/app/profile.json` へ JSON 保存。未存在時はサンプル `WAKE Guest` を自動生成して UX を途切れさせない。
- **依存ライブラリ**: LangChain の `ChatOpenAI` を継続利用。02 ではプロフィール文脈を組み立てるヘルパを追加し、`OPENAI_API_KEY` 未設定時はフェイク応答で落ちないようにした。
- **health 応答**: `{"ok": true}` から `{"ok": true, "phase": "02_profile_api"}` に拡張し、フロントでフェーズ表示・疎通確認をしやすくした。
- **フロント UI**: LLM ping フォームは撤去し、プロフィール編集フォーム＋「LLM にキャリア相談」セクションに差し替え。保存値を自動ロード/反映し、回答プロバイダー（openai/fake）も表示。
- **スタイルの微調整**: `.shell` ラッパで横幅を `min(760px, 92vw)` にし、モバイルでも左右に余白を確保。カード/パネル構成は 01 のトーンを踏襲しつつ改修。

### コードレベルの差分（ファイル別に一つずつ）
- `backend/app/main.py`
  ```diff
  -@app.post("/api/ping-llm")
  -def ping_llm(...):
  -    llm = ChatOpenAI(...)
  -    out = llm.invoke([{"role":"user","content": payload.prompt}])
  -    return {"reply": out.content}
  +@app.get("/api/profile")
  +def get_profile():
  +    return _load_or_create_profile()
  +
  +@app.put("/api/profile")
  +def upsert_profile(...):
  +    DATA_FILE.write_text(...)
  +
  +@app.post("/api/profile/advice")
  +def get_profile_advice(payload):
  +    profile = _load_or_create_profile()
  +    messages = [
  +      SystemMessage(...プロンプト...),
  +      HumanMessage(...プロフィール要約 + 質問...),
  +    ]
  +    llm = ChatOpenAI(model=..., api_key=...)
  +    return {"provider": "openai", "answer": llm.invoke(messages).content}
  ```
  - LLM 呼び出しは LangChain/ChatOpenAI 継続だが、自由入力 → プロフィール埋め込み型に変化。
  - `DEFAULT_PROFILE` を追加し、未保存でも初回アクセスで自動生成。

- `backend/pyproject.toml` / `backend/requirements.txt` / `backend/uv.lock`
  - 依存パッケージは 01 と同じく `langchain-openai` を採用（生 `openai` SDK には移行していない）。02 ではこの上にプロフィール要約ヘルパとフェイク応答を積み増し。

- `frontend/src/main.tsx`
  ```diff
  - const [prompt, setPrompt] = useState(...)
  - <textarea ... onChange={setPrompt} />
  - <button onClick={handlePing}>LLM に送る</button>
  + const [form, setForm] = useState<Profile>({...})
  + const [question, setQuestion] = useState('次に身につけた方が良いスキルは？')
  + const [advice, setAdvice] = useState(null)
  + await fetch('/api/profile', { method: 'PUT', body: form })
  + await fetch('/api/profile/advice', { method: 'POST', body: { question } })
  + <pre>{advice?.answer}</pre>
  ```
  - LLM 直叩き UI を廃し、プロフィール CRUD + アドバイス取得に一本化。

- `frontend/src/style.css`
  ```diff
  +.shell {
  +  max-width: 760px;
  +  width: min(760px, 92vw);
  +  margin: 2rem auto;
  +  padding: 1.5rem;
  +}
  ```
  - 01 の `.app-shell` は使わず、02 専用ラッパで左右ガッターを確保。

- `README.md`
  ```diff
  +## 01_bootstrap との実装差分 ...
  +...プロフィール保存/取得/アドバイスの手順と OpenAI 設定を追記...
  ```
  - 01 では LLM 疎通のみだった説明を、02 ではプロフィール永続化＋アドバイス取得手順まで教材化。

## プロフィールを LLM に渡す流れ（02 の肝）

### コード差分で見る
```diff
@@ backend/app/main.py @@
 def _load_or_create_profile() -> ProfileResponse:
   if not DATA_FILE.exists():
     default = ProfileResponse(**DEFAULT_PROFILE.model_dump())
     DATA_FILE.write_text(default.model_dump_json(indent=2, ensure_ascii=False))
     return default
   return ProfileResponse(**json.loads(DATA_FILE.read_text()))

 def _build_prompt(profile, question):
   profile_summary = f"...氏名: {profile.name}\\n経験年数: {profile.years}年...\\nスキル: {', '.join(profile.skills)}..."
   system = "あなたは日本語で回答するキャリアコーチです。...箇条書きで400文字以内..."
   user_prompt = f\"プロフィール:\\n{profile_summary}\\n\\n相談内容: {question}\"
   return [
     {"role": "system", "content": system},
     {"role": "user", "content": user_prompt},
   ]

 def _call_openai(messages):
   llm = ChatOpenAI(model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"), api_key=os.getenv("OPENAI_API_KEY"), temperature=0.4)
   res = llm.invoke([SystemMessage(content=messages[0]["content"]), HumanMessage(content=messages[1]["content"])])
   return str(res.content or "")

 @app.post("/api/profile/advice")
 def get_profile_advice(payload):
   profile = _load_or_create_profile()
   messages = _build_prompt(profile, payload.question)
   answer = _call_openai(messages) if os.getenv("OPENAI_API_KEY") else _fake_answer(profile, payload.question)
   return AdviceResponse(provider="openai" if os.getenv("OPENAI_API_KEY") else "fake", answer=answer)
```

### 実例（リクエスト/レスポンス）
1. プロフィールを保存（未保存なら自動生成されるので省略可）
```bash
curl -X PUT http://localhost:28089/api/profile \
  -H "Content-Type: application/json" \
  -d '{"name":"Alice","years":6,"current_role":"Backend Engineer","target_role":"AI PM","skills":["Python","FastAPI"],"interests":["RAG","Career"],"notes":"LLM活用に興味"}'
```
2. アドバイスを取得
```bash
curl -X POST http://localhost:28089/api/profile/advice \
  -H "Content-Type: application/json" \
  -d '{"question":"次の3ヶ月でやるべきことは？"}'
```
3. 典型レスポンス（OpenAI キーありの場合）
```json
{
  "provider": "openai",
  "answer": "- プロダクト思考の強化として、社内のAI案件でPMロールを1タスク担当する\n- Python/FastAPIでミニAPIを作り、RAGを組み込んでPoC化する\n- 週1でAI PM事例をリサーチし、学びをノートにまとめて共有する"
}
```
キー未設定なら `"provider": "fake"` でフォールバックし、同スキーマで返ります。

## できること（API）
- `/api/health` … フェーズ確認
- `/api/profile` … プロフィール保存/取得（JSON ファイル直書き）
- `/api/profile/advice` … 保存済みプロフィールをプロンプトに埋め込み、LLM からキャリアアドバイスを取得（`OPENAI_API_KEY` 未設定時はフェイク生成）
  - プロフィール未設定でも初回アクセス時にサンプル（WAKE Guest）を自動生成するので、そのまま試せます。

## コードの見どころ
- backend: `app/main.py` で Pydantic モデルを定義し、ローカル JSON (`profile.json`) へ読み書き。
- 将来の DB 切替に備え、I/O を関数で分離しているので Step03 以降に差し替えやすい構造。
- frontend: フォーム入力→保存→再読込で値が残るシンプル UI。

## 起動手順（最短）
```bash
cd 02_profile_api
make dev   # 初回は内部で uv run / npm install が走ります
```

高速化したい場合（依存を事前導入）
```bash
cd 02_profile_api/backend && uv sync && cd ..
cd frontend && npm install && cd ..
make dev
```
デフォルトポートは backend 28089 / frontend 25073。競合する場合は `BACKEND_PORT` / `FRONTEND_PORT` を上書きしてください。

### OpenAI を使う場合
環境変数に API キーをセットしてください（モデルは `OPENAI_MODEL` で上書き可、デフォルト `gpt-4o-mini`）。
```bash
export OPENAI_API_KEY=sk-xxxxx
export OPENAI_MODEL=gpt-4o-mini  # 省略可
```
