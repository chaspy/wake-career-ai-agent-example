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
```

## 仕組みの要点
- 記事/RAG 部分は Step03 と同じ（FAISS ロード＋類似検索）。
- 求人は fake 実装（サンプル3件をクエリ・ロケーションに合わせて返却）。live 化したい場合は `jobs` ロジックを差し替えれば踏み台になります。
- health が `mode`/`provider` を返すので、fake か live か UI から判別可能。

## フロントの流れ
1. 左: 記事リスト → 詳細。
2. 中: RAG クエリ入力 → 推薦カード（score / 抜粋 / 理由）。
3. 右: 求人キーワード入力 → fake ジョブカード（会社・ロケーション・説明）。

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
- 求人検索 API（フェイク実装）を新設。キーワード・ロケーションを受けてサンプル求人を返すだけなので、実サービスに差し替える足場になる。
  ```py
  # backend/app/routers/jobs.py 抜粋
  @router.post("/api/jobs/search", response_model=JobSearchResponse)
  async def search_jobs(payload: JobSearchRequest) -> JobSearchResponse:
      q = (payload.query or "エンジニア").strip()
      loc = (payload.location or "Tokyo").strip()
      jobs = _fake_jobs(q, loc)
      return JobSearchResponse(
          jobs=jobs[: payload.limit],
          sources=sorted({job.url for job in jobs}),
          queries=[q],
      )
  ```
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
2. `backend/app/routers/jobs.py` の `_fake_jobs` を実求人 API クライアントに差し替えると、UI はそのまま流用可能。
3. LangChain 部分を拡張したい場合は `backend/app/rag/` 配下のモジュールを参照。FAISS の入替や再インデックスなどは 03 と同じ手順で OK。
