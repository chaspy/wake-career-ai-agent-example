# 04_recommend_rag

前フェーズとの差分: RAG に加えて求人検索を追加。ここで「おすすめ記事 + 求人」の双方向を見るステップ。
- `/api/articles`・`/api/articles/{slug}` … 03 と同じ
- `/api/recommendations` … FAISS 検索＋ fake/live 理由生成
- `/api/jobs/search` … Wantedly/Remotive から求人を取得（キーワード・ロケーション）

## 起動手順

### 推奨: backend / frontend を個別に起動

1. 依存導入とシード（初回のみ）
   ```bash
   cd 04_recommend_rag/backend
   uv sync
   MODE=fake DB_MODE=sqlite uv run python scripts/seed.py
   ```
   - OpenAI / DB を本番モードで使いたい場合は `MODE=live` や `DB_MODE=json` に変更してください。

2. バックエンド
   ```bash
   cd 04_recommend_rag/backend
   MODE=fake DB_MODE=sqlite uv run uvicorn uvicorn_app:app --reload --host 0.0.0.0 --port 48089
   ```
   - `MODE=fake` なら OpenAI キー無しでもオフライン理由生成で動きます。live にする場合は `export OPENAI_API_KEY=...` とモデル設定を行ってください。

3. フロントエンド
   ```bash
   cd 04_recommend_rag/frontend
   npm install
   VITE_API_BASE=http://localhost:48089 npm run dev -- --host 0.0.0.0 --port 45073
   ```

4. ブラウザで http://localhost:45073 を開き、記事/RAG/求人の 3 カラムを確認。

### make が使える場合

```bash
cd 04_recommend_rag
MODE=fake DB_MODE=sqlite make dev   # backend 48089 / frontend 45073
```

ポート衝突時は `BACKEND_PORT` / `FRONTEND_PORT` を一緒に指定してください。

## 仕組みの要点
- 記事/RAG 部分は Step03 と同じ（FAISS ロード＋類似検索）。
- 求人は Wantedly（HTML の構造化データ）と Remotive（REST API）から直接取得し、重複除去・クエリマッチ・スコアリングして返却。fake モードは「求人取得は本番のまま、LLM スコアリングのみオフライン評価」に落ちる。
- health が `mode`/`provider` を返すので、fake か live か UI から判別可能。

## フロントの流れ
1. 左: 記事リスト → 詳細。
2. 中: RAG クエリ入力 → 推薦カード（score / 抜粋 / 理由）。
3. 右: 求人キーワード入力 → Wantedly/Remotive 由来のジョブカード（会社・ロケーション・説明）。

「おすすめを取得（ダミー）」でカード表示されれば準備完了。ポート競合時は環境変数で変更してください。

---

## 学習メモ（03_articles_ingest → 04_recommend_rag の差分）

### バックエンドの主な追加点
- ルータ分割: `routers/articles.py`, `recommend.py`, `profile.py` に加え新規 `jobs.py` を登録。CORS にフロントポート（45073）を追加し、preflight 400 を解消。
- プロフィール永続化を抽象化: `db.py` で SQLite / JSON をサポート。起動時にデフォルトプロフィールを自動生成。
  ```py
  # backend/app/db.py 抜粋
  DEFAULT_PROFILE = Profile(
      name="WAKE Career Demo",
      years=7,
      current_role="Product Manager",
      target_role="AI Product Manager",
      ...
  )
  def ensure_profile(self, default: Profile = DEFAULT_PROFILE) -> None:
      if self.get_profile() is None:
          self.save_profile(default)
  ```
- 求人検索 API を新設。`search_jobs` が Wantedly/Remotive から取得した求人を評価・重複除去して返却する（ロジックは `backend/app/jobs/__init__.py` に集約）。
- LangChain/RAG 部分は 03 と同じ FAISS 検索＋embedding（OpenAI or Fake）。追加の LLM 呼び出しはなし ― 差分なしであることを明示。

### フロントの主な追加点
- 画面を 3 カラム化しコンポーネント分割（記事一覧・RAG推薦・求人）。`JobList`, `AgentActivity`, `ProfileForm`, `RecoList` などを新設。
- プロフィールは API 取得後に自動でフォームへ反映され、入力なしで「おすすめを取得」を試せる。
  ```tsx
  // frontend/src/components/ProfileForm.tsx 抜粋
  useEffect(() => {
    if (!profile) return
    setDraft({ ...profile, notes: profile.notes ?? '' })
    setSkillsInput(profile.skills.join(', '))
    setInterestsInput(profile.interests.join(', '))
  }, [profile])
  ```
- 求人フェッチを記事推薦と同時に実行し、試行クエリ・取得元を表示。
  ```tsx
  // frontend/src/pages/Home.tsx 抜粋
  const jobResponse = await searchJobs({ profile: readyProfile ?? undefined, query: query || undefined, limit: 10 })
  setJobs(jobResponse.jobs)
  setJobSources(jobResponse.sources)
  setJobQueries(jobResponse.queries ?? [])
  ```
- `Makefile` で `VITE_API_BASE="http://localhost:$(BACKEND_PORT)"` を注入し、フロント/バックのポートずれを解消。

### 変わらないもの
- RAG の検索ロジック・スコア算出・引用整形は 03 と同じ。
- Embedding フォールバック（OpenAI 未設定時は FakeEmbeddings）、FAISS のロード/保存の扱いも共通。

### 触って学ぶポイント
1. `make dev` で 48089/45073 を起動し、初期プロフィールのまま「おすすめを取得」を押す。
2. 別の求人ソースに差し替える場合は `backend/app/jobs/__init__.py` の `_fetch_wantedly` / `_fetch_remotive` を新 fetcher に置き換えるだけで UI を流用可能。
3. LangChain 部分を拡張したい場合は `backend/app/rag/` 配下のモジュールを参照。FAISS の入替や再インデックスなどは 03 と同じ手順で OK。

## 求人取得ロジック（Wantedly / Remotive）
- 実装ファイル: `backend/app/jobs/__init__.py`
- フロー概要: `search_jobs` → `_fetch_jobs` が Wantedly と Remotive を順に叩き、結合・重複除去・クエリマッチ → `_evaluate_jobs` でスコア付け → `_rank_jobs` で 0.6 以上を返却。
- Wantedly 取得: `_fetch_wantedly` にて `https://www.wantedly.com/projects` を `keyword` 付きで HTML GET。`<script type="application/ld+json">` の `ItemList` を JSON パースし、`title/company/url/datePosted/jobLocation.address` を `JobSummary` に詰める。`_strip_html` で description を平文化、`_normalize_datetime` で UTC ISO に揃える。
- Remotive 取得: `_fetch_remotive` にて `https://remotive.com/api/remote-jobs` を `search`/`location` パラメータ付きで呼び、JSON の `jobs` 配列から `title/company_name/url/publication_date/candidate_required_location` を取り込む。
- 並び順とフィルタ: `_job_sort_key` で新着優先にソートし、URL 重複を除外。クエリがある場合は `_matches_keyword` で `title/company/snippet` にトークンヒットするものを優先。足りない場合は重複しないものを追加。
- スコアリング: live モード + OpenAI キー有りなら LLM 評価（PydanticOutputParser で 0-1 スコアと refine_query を返す）。それ以外ではキーワードヒット数ベースの決定的スコア。0.6 以上のみを返し、なければ再検索/フォールバックで最大 3 回試行。
- タイムアウトと冗長性: `FETCH_TIMEOUT=8` 秒で UI 待ちを短縮。片方のソースが落ちてももう一方の結果で続行し、失敗ログは `[jobs] fetcher failed: ...` として標準出力に残す。

## LangGraph をどこで何のために使っているか
- 役割: RAG 推薦の一連のステップ（クエリ生成 → 検索 → LLM で理由生成 → レスポンス成形）をステートマシンとして明示するために採用。失敗時にフェイク応答へフォールバックする分岐もここで管理。
- 実装場所: `backend/app/rag/graph.py`
- ノード構成（StateGraph）:
  ```py
  graph.add_node("build_query", _build_query)   # プロフィール/入力から検索クエリを組み立て
  graph.add_node("retrieve", _retrieve)         # FAISS（Retriever）で上位 k を取得
  graph.add_node("call_model", _call_model)     # live: ChatOpenAI へ投げる / no-key: offline_answer で理由生成
  graph.add_node("respond", _respond)           # 空結果の埋め草や JSON 形に整形
  graph.set_entry_point("build_query")
  graph.add_edge("build_query", "retrieve")
  graph.add_edge("retrieve", "call_model")
  graph.add_edge("call_model", "respond")
  graph.add_edge("respond", "__end__")
  ```
- 遷移図（Mermaid）:
  ```mermaid
  flowchart TD
    A([build_query]) --> B[retrieve<br/>FAISS で k 件取得]
    B --> C{documents > 0?}
    C -->|yes & live| D[call_model<br/>ChatOpenAI + PydanticOutputParser]
    C -->|yes & fake| E[offline_answer]
    C -->|no| F[空リスト]
    D --> G[respond<br/>空配列なら no-data を補填]
    E --> G
    F --> G
    G --> H([__end__])
  ```
- LLM 呼び出し（live モードのみ）:
  - `ChatOpenAI(model=settings.openai_model, temperature=0.2)` を使用。
  - PydanticOutputParser（`LLMResponse`）で JSON 形式を強制し、推薦理由を3観点で返す。
  - 成功しない場合や fake モードでは `offline_answer` が deterministic な理由文を生成。
- ここで扱うのは「推薦カード生成」専用フロー。求人検索やフロントのステージ表示とは独立しており、LangGraph を足がかりにプランニング等のワークフローを後続フェーズに拡張できる構成。

### FAQ: なぜ LangGraph が必要？ LangChain だけでは？
- LangChain の `chain`/`LCEL` だけでも直列フローは書けるが、分岐と再試行を伴うステート管理（例: documents 0 件ならフェイク応答、LLM 失敗時リトライなど）を明示するのが難しい。
- LangGraph は状態遷移（ノード・エッジ）を宣言的に書けるため、「どこで何が起きるか」「どこでフォールバックするか」を図とコードの両方で揃えやすい。
- 追加メリット: 将来的なステップ追加（再ランキング、クエリ再生成など）や条件付き分岐を差分だけで増築しやすく、デバッグ時もどのノードで落ちたかを特定しやすい。
- 本プロジェクトでは `build_query → retrieve → call_model → respond` の直列だが、LangGraph を使うことで「live/fake」「データ無し」の経路をコードと Mermaid 図の両方で示し、後続フェーズでの拡張に備えている。

### 実コードで読む（抜粋）

```py title="backend/app/rag/graph.py"
def build_recommendation_graph():
    graph = StateGraph(GraphState)
    graph.add_node("build_query", _build_query)   # プロフィール/入力からクエリ生成
    graph.add_node("retrieve", _retrieve)         # FAISS で候補記事を取得
    graph.add_node("call_model", _call_model)     # LLM で理由生成 or offline_answer
    graph.add_node("respond", _respond)           # 空結果補填・最終整形
    graph.set_entry_point("build_query")
    graph.add_edge("build_query", "retrieve")
    graph.add_edge("retrieve", "call_model")
    graph.add_edge("call_model", "respond")
    graph.add_edge("respond", "__end__")
    return graph.compile()
```

```py title="backend/app/rag/graph.py"
llm = ChatOpenAI(model=settings.openai_model, temperature=0.2, api_key=settings.openai_api_key)
parser = PydanticOutputParser(pydantic_object=LLMResponse)
prompt = ChatPromptTemplate.from_messages([...])  # プロフィール/検索文脈を詰め込む
chain = prompt | llm | parser                     # LangChain Expression Language
llm_response = chain.invoke({
    "profile": profile_text,
    "query": query,
    "context": context,        # 上位k記事の本文スニペット
    "top_k": top_k,
    "format_instructions": parser.get_format_instructions(),
})
```

```py title="backend/app/rag/fake_model.py"
def offline_answer(documents: list[Document], profile: Profile | None, top_k: int):
    # OpenAI キーが無いときのフォールバック。決定論的に理由を生成して UI を埋める。
```

求人 API との接続（バックエンド・フロント）もコード付きで追えるようにしておきます。

```py title="backend/app/routers/jobs.py"
@router.post("/api/jobs/search", response_model=JobSearchResponse)
async def search_jobs(payload: JobSearchRequest) -> JobSearchResponse:
    q = (payload.query or "エンジニア").strip()
    loc = (payload.location or "Tokyo").strip()
    jobs = _fake_jobs(q, loc)          # ←ここを実求人クライアントに差し替えれば OK
    return JobSearchResponse(
        jobs=jobs[: payload.limit],
        sources=sorted({job.url for job in jobs}),
        queries=[q],
    )
```

```tsx title="frontend/src/pages/Home.tsx"
const jobResponse = await searchJobs({
  profile: readyProfile ?? undefined,
  query: query || undefined,
  limit: 10,
})
setJobs(jobResponse.jobs)
setJobSources(jobResponse.sources)
setJobQueries(jobResponse.queries ?? [])
```
