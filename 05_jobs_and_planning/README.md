# 05_jobs_and_planning

05 フェーズは **04_recommend_rag** をベースに、面談準備までをワンストップで支援する「プランニング層」をフロントエンドに載せた最終確認用スナップショットです。

## このフォルダの扱い

- ここにコードは置かれていません（`backend/` 配下はベクトルストアなどのデータのみ）。実際に動かす際はリポジトリ直下（= 完成版）の `backend/` / `frontend/` を使ってください。
- `04_recommend_rag` と比較しやすいよう、README では UI/UX と実装観点の差分をまとめています。コードを追う際はルートディレクトリと該当ファイルを開いてください。
- RAG 用データを個別に確認したい場合は、ここに置いた `backend/data/`（FAISS/Chroma・サンプル DB）を参照すれば 05 時点のベースラインを確認できます。

## 04 → 05 の主な差分

- **プランニングエージェントを LangGraph + FastAPI で追加**: `/api/plan` が推薦・求人を受け取り、live では OpenAI / fake では決定論的テンプレでプランを返します（`backend/app/planner/graph.py`、`backend/app/routers/plan.py`、`backend/app/tests/test_plan.py`）。
- **フロントから Planner を起動しプランボード描画**: 記事/求人取得後に Planner を呼び、ログを可視化して面談用プランボードへ反映します（`frontend/src/pages/Home.tsx:115-213, 322-395`）。
- **AgentActivity の 3 レーン化**: 推薦・求人・プランニングの進行を並列表示し、plan → synthesize → validate → done を段階表示します（`frontend/src/components/AgentActivity.tsx`）。
- **求人クエリ/ソースの受け渡し強化**: Job エージェントの試行クエリと取得元を Planner/プランボードにも共有するよう整理しました（`frontend/src/pages/Home.tsx` の jobStage 処理周辺）。
- **初期プロフィールとポート設定の更新**: サンプルを WAKE Guest に差し替え、デフォルトポートを backend 8089 / frontend 5173 に統一し CORS も合わせました（`backend/app/db.py:28-36`、`backend/app/config.py`、`Makefile`）。

## コード差分の見どころ

- `backend/app/planner/graph.py`, `backend/app/routers/plan.py`  
  - LangGraph で「prepare → call_model → finalize」のシンプルなステートマシンを構築。live: OpenAI で JSON 生成、失敗/キーなし: オフラインテンプレにフォールバック。
- `backend/app/tests/test_plan.py`  
  - `/api/plan` が fake モードでもレポートを返すことを検証し、最終フェーズのフェイルセーフを担保。
- `frontend/src/pages/Home.tsx`  
  - `plannerStage` と `fetchPlan` 呼び出しを組み込み、推薦→求人→プラン生成を一連で実行。PlanReport を受け取りプランボードへ描画。
- `frontend/src/components/AgentActivity.tsx`  
  - Planner レーンの追加とログ表示を共通化し、ステージの色分け/バッジを拡充。
- `frontend/src/App.css`  
  - プランボード用の `.plan-section`/`.plan-grid`/`.option-table` などを追加し、カードレイアウトに調整。

## 代表的なスニペット

### 推薦→求人→プランのステージ制御（`frontend/src/pages/Home.tsx`）

```tsx
const handleRecommend = async () => {
  setPlannerStage('plan');
  const jobResponse = await searchJobs(...);
  const recoResponse = await fetchRecommendations(...);
  if (recoResponse.recommendations.length > 0) {
    const planResponse = await fetchPlan({
      profile: readyProfile ?? undefined,
      recommendations: recoResponse.recommendations,
      jobs: jobResponse.jobs,
    });
    planResponse.logs.forEach((entry) => logActivity(`Planner: ${entry}`));
    setPlanReport({
      profileInsights: planResponse.profileInsights,
      careerOptions: planResponse.careerOptions,
      learning: planResponse.learning,
      actions: planResponse.actions,
      selfCheck: planResponse.selfCheck,
    });
    setPlannerStage('done');
  }
};
```

### AgentActivity へのレーン追加（`frontend/src/components/AgentActivity.tsx`）

```tsx
<div className="agent-trail">
  <div className="agent-row">
    <span className={statusDot(plannerStage === 'error' ? 'error' : plannerStage === 'done' ? 'done' : plannerStage === 'idle' ? 'idle' : 'active')} />
    <div>
      <p className="agent-label">プランニングエージェント</p>
      <p className="agent-status">
        {plannerStage === 'plan'
          ? '推薦記事と求人を読み込み、学習/行動プランの骨子を整理中…'
          : plannerStage === 'synthesize'
            ? '要点を抽出し、プロフィールに合わせて優先順位付け中…'
            : plannerStage === 'validate'
              ? '自己検証チェックリストを追加中…'
              : plannerStage === 'error'
                ? `エラー: ${plannerError}`
                : plannerStage === 'done'
                  ? '初回面談用のプランを作成しました。下部のプランボードを確認できます。'
                  : 'まだ実行していません。おすすめ取得後に自動で走ります。'}
      </p>
      <div className="agent-steps">
        <span className={`agent-chip ${stageToChip(plannerStage, 'plan')}`}>インプット整理</span>
        <span className={`agent-chip ${stageToChip(plannerStage, 'synthesize')}`}>要約/優先度付け</span>
        <span className={`agent-chip ${stageToChip(plannerStage, 'validate')}`}>自己検証</span>
      </div>
    </div>
  </div>
</div>
```

## LangGraph の扱い

- 推薦用 LangGraph（`backend/app/rag/graph.py`）は 04 と同じ直列フロー（build_query → retrieve → call_model → respond）。fake では offline_answer へフォールバック。
- 05 で新設したプランニング LangGraph（`backend/app/planner/graph.py`）は prepare → call_model → finalize の 3 ノード構成。live: OpenAI で PlanReport を生成、fake: 決定論的テンプレートで必ず 1 プランを返します。

## 起動・シード手順（完成版）

### 推奨: backend / frontend を個別に起動（リポジトリ直下）
1. `.env` を用意（未作成なら `cp .env.sample .env`）し、必要に応じて `OPENAI_API_KEY` を設定。
2. バックエンド
   ```bash
   cd backend
   uv sync
   MODE=fake DB_MODE=sqlite uv run python scripts/seed.py   # 初回のみ
   MODE=fake DB_MODE=sqlite uv run uvicorn uvicorn_app:app --reload --host 0.0.0.0 --port 8089
   ```
3. フロントエンド
   ```bash
   cd frontend
   npm install
   VITE_API_BASE=http://localhost:8089 npm run dev -- --host 0.0.0.0 --port 5173
   ```
4. ブラウザで http://localhost:5173 を開く。OpenAI を使う場合は `MODE=live` にし、`.env` へ API キーを設定してください。

### make が使える場合

```bash
MODE=fake DB_MODE=sqlite make dev   # backend:8089 / frontend:5173
make seed                           # ベクトルストア生成（初回のみ）
```

- Windows は WSL2、それ以外は macOS/Linux を推奨。GitHub Codespaces と macOS でのみ動作確認済みです。

## 触って学ぶチェックポイント

- 「おすすめを取得」を押し、AgentActivity で 3 レーンが進む様子と Planner のログコピーを確認。
- プロフィールや求人キーワードを変えて「おすすめを取得」を再実行し、プランボードの Learning / Action / Self-check がどう変わるか確認。
- 04 の UI と比較し、RAG+求人は据え置きのまま、バックエンドに LangGraph Planner を足してフロントでログ/プラン表示を拡張した構成を確認。

## 学習ポイント

- **決定論的 Planner でフェイルセーフ**: LLM が不調でも、テンプレベースのプラン生成によって最低限の提案が返せる。
- **三段パイプラインの可視化**: プランニングを含めたステージ管理を UI で見せることで、LangGraph 的なグラフ実行の理解が進む。
- **データ/構成のレバレッジ**: バックエンドは 04 と同等のまま、UI とサンプルデータを工夫するだけでユーザ体験を大きく変えられることを確認できます。
