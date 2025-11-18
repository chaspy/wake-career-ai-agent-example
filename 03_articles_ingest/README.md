# 03_articles_ingest

前フェーズとの差分: 01/02 のプロフィール管理＋LLM アドバイスを残したまま、記事インジェストと RAG 推薦を追加。
- `/api/profile` (GET/PUT) … プロフィールの保存/取得。`backend/app/data/profile.json` に永続化。
- `/api/profile/advice` … 保存済みプロフィールをプロンプトに差し込み、fake もしくは OpenAI で回答。
- `/api/articles` … Markdown 記事の一覧
- `/api/articles/{slug}` … 記事本文取得
- `/api/recommendations` … ベクトル検索＋ fake/live 理由生成
- サンプル記事: `backend/app/data/articles/sample.md`

## 起動手順（最短）
```bash
cd 03_articles_ingest
make dev   # 初回は内部で uv run / npm install が走ります
```

RAG 用ベクトルストアを作る（初回だけでOK）
```bash
cd 03_articles_ingest/backend && uv sync && uv run python scripts/seed.py && cd ..
cd frontend && npm install && cd ..
make dev
```
デフォルトポート: backend 38089 / frontend 35073。競合時は `BACKEND_PORT` / `FRONTEND_PORT` を上書きしてください。

## 仕組みの要点
- プロフィール: `/api/profile` が JSON を読み書き、`/api/profile/advice` は保存済みプロフィールをプロンプトに入れて ChatOpenAI（キー未設定時は fake テキスト）を叩きます。
- seed: `scripts/seed.py` が markdown をチャンク分割（LangChain TextSplitter）し、FAISS へ保存。OpenAI キーなしは FakeEmbeddings、ありは text-embedding-3-small。
- 推薦: `/api/recommendations` は FAISS の類似検索を叩き、fake 時は固定文言、live 時は ChatOpenAI で理由生成。
- mode/provider: health で `fake/live` を返すので、UI 側で状態表示できます。

## 02→03 のコード差分（解説＋スニペット）
### バックエンド
**プロフィール機能は継承（保存先だけ変更）**  
`/api/profile` は 02 と同じスキーマ・プロンプトを維持しつつ、保存先が `data/profile.json` に変わりました。デフォルトプロフィールを同梱済み。
```python
# backend/app/main.py:125-189,224-243 の抜粋
@app.put("/api/profile")
def upsert_profile(payload: Profile):
    PROFILE_FILE.write_text(payload.model_dump_json(indent=2, ensure_ascii=False), encoding="utf-8")
    return ProfileResponse(**payload.model_dump())

def _build_prompt(profile: ProfileResponse, question: str) -> List[dict[str, str]]:
    profile_summary = (
        f"氏名: {profile.name}\n…\nノート: {profile.notes or 'なし'}"
    )
    system = "あなたは日本語で回答するキャリアコーチです。…"
    return [{"role": "system", "content": system},
            {"role": "user", "content": f"プロフィール:\n{profile_summary}\n\n相談内容: {question}"}]
```

**Embeddings とベクトルストア読み込み**  
OpenAI キー有無で埋め込みを切替え、FAISS の `index.faiss/index.pkl` をロード（初回は `scripts/seed.py` で生成）。
```python
# backend/app/main.py:100-113
@lru_cache(maxsize=1)
def get_vectorstore() -> FAISS:
    index_file = VSTORE_DIR / "index.faiss"
    if not index_file.exists():
        raise FileNotFoundError("vectorstore not seeded; run `uv run python scripts/seed.py`")
    return FAISS.load_local(str(VSTORE_DIR), _embedding_fn(), allow_dangerous_deserialization=True)

def _embedding_fn():
    if os.getenv("OPENAI_API_KEY"):
        return OpenAIEmbeddings(model="text-embedding-3-small")
    return FakeEmbeddings(size=1536)
```

**RAG 推薦 API**  
FAISS の距離スコアを 0〜1 類似度に正規化して返却。複数チャンクから拾った本文先頭を excerpt に入れ、引用元 URL も付与。
```python
# backend/app/main.py:151-176
docs = store.similarity_search_with_score(payload.query, k=payload.top_k)
for doc, score in docs:
    distance = float(score)
    similarity = 1.0 / (1.0 + distance)  # 0~1 に見やすく正規化
    recs.append(Recommendation(
        slug=meta.get("slug", ""), title=meta.get("title", "Untitled"),
        url=meta.get("source_url", ""), score=similarity,
        excerpt=doc.page_content[:240],
        reasons=_make_reasons(doc.page_content, payload.query),
        citations=[meta.get("source_url", "")]
    ))
```

**推薦理由の生成**  
キー無しなら固定文、キーありなら ChatOpenAI で 1 文サマリ。02 のアドバイスと同じくシンプルな system + user プロンプト構成。
```python
# backend/app/main.py:211-221
def _make_reasons(text: str, query: str) -> List[str]:
    if not os.getenv("OPENAI_API_KEY"):
        return [f"fake: '{query}' と関連しそうな本文を抽出しました"]
    llm = ChatOpenAI(model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"), temperature=0)
    prompt = ("ユーザの関心と本文を渡すので、1文で推薦理由を出してください。必ず日本語で簡潔に。\n"
              f"[query]\n{query}\n[context]\n{text[:500]}")
    out = llm.invoke([{"role": "user", "content": prompt}])
    return [out.content]
```

**記事インジェスト**  
02 には無かったチャンク分割＋ベクトル化処理を `ingest_articles` に追加。`seed.py` から再利用。
```python
# backend/app/main.py:260-289
splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=80)
for chunk in splitter.split_text(post.content):
    docs.append({"page_content": chunk,
                 "metadata": {"title": title, "source_url": source, "slug": slug}})
vs = FAISS.from_documents([Document(**d) for d in docs], _embedding_fn())
vs.save_local(str(vector_dir))
```

### フロントエンド
**プロフィール＋RAG を同一画面に統合**  
02 のプロフィール/アドバイス UI を残しつつ、記事一覧（横スクロール風リスト）と RAG カードをページ上部に配置。ボタンのローディング表示も追加。
```tsx
// frontend/src/main.tsx 抜粋
const [adviceLoading, setAdviceLoading] = useState(false);
const askAdvice = async () => {
  setAdviceLoading(true); setStatus('LLM 呼び出し中...');
  const res = await fetch('/api/profile/advice', { method: 'POST', ... });
  const data: AdviceResponse = await res.json();
  setAdvice(data); setStatus(`回答取得 (${data.provider})`);
  setAdviceLoading(false);
};

<section className="card reco full">…</section>  // RAG 推薦を全幅で表示
<section className="card">…記事一覧を横方向リストで表示…</section>
```

**変わっていないこと**  
- プロフィールスキーマ、アドバイス用プロンプトの構造、Fake/Live の分岐は 02 と同じ思想。  
- FastAPI + Pydantic の型付け、フロントの fetch ベース API 呼び出しスタイルも踏襲。


## フロントの流れ
1. プロフィールを入力して保存 → `/api/profile` PUT。
2. 「LLM にキャリア相談」で `/api/profile/advice` を叩き、保存済みプロフィールを差し込んだ回答を表示。
3. `/api/articles` でリスト化 → クリックで `/api/articles/{slug}` 詳細表示。
4. クエリ入力後「おすすめを取得」→ `/api/recommendations` POST → スコア・理由つきカード表示。
