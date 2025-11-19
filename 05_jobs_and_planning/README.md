# 05_jobs_and_planning

05 フェーズは **04_recommend_rag** をベースに、面談準備までをワンストップで支援する「プランニング層」をフロントエンドに載せた最終確認用スナップショットです。

## このフォルダの扱い

- ここにコードは置かれていません（`backend/` 配下はベクトルストアなどのデータのみ）。実際に動かす際はリポジトリ直下（= 完成版）の `backend/` / `frontend/` を使ってください。
- `04_recommend_rag` と比較しやすいよう、README では UI/UX と実装観点の差分をまとめています。コードを追う際はルートディレクトリと該当ファイルを開いてください。
- RAG 用データを個別に確認したい場合は、ここに置いた `backend/data/`（FAISS/Chroma・サンプル DB）を参照すれば 05 時点のベースラインを確認できます。

## 04 → 05 の主な差分

- **プランニングエージェントの追加（フロントのみ）**: 記事推薦・求人結果を入力に、学習/行動/自己検証チェックを決定論的ロジックで生成し、「面談用プランボード」として描画します（`frontend/src/pages/Home.tsx:116-207, 375-447`）。
- **AgentActivity の 3 レーン化**: 推薦・求人・プランニングの進行を並列表示し、plan → synthesize → validate → done の各段階とエラーを可視化します（`frontend/src/components/AgentActivity.tsx:3-137`）。
- **求人連携の強化**: Job エージェントの探索クエリや取得ソースを Planner が参照できるようにし、プラン生成の文脈へ引き継ぎます（`frontend/src/pages/Home.tsx:205-256`）。
- **初期プロフィールを WAKE Guest へ刷新**: 参加者がキー未設定でも動かしやすいサンプルプロフィールに変更しました（`backend/app/db.py:26-43`）。
- **ポート/CORS/Makefile の最終化**: backend 8089 / frontend 5173 をデフォルトにし、`backend/app/config.py:25-28` で allowed_origins を揃えています。

## コード差分の見どころ

- `frontend/src/pages/Home.tsx`  
  - `PlanReport` 型、`plannerStage` ステート、`buildPlanReport` ヘルパを追加し、推薦→求人→プランニングの 3 段パイプラインを構築。
  - `handleRecommend` 内で Planner を明示的に発火し、ログ/アニメーションを LangGraph 風に見せています。
- `frontend/src/components/AgentActivity.tsx`  
  - Planner 用のバッジとステージドットを追加し、他エージェントと同じログストリームを使い回す設計。
- `frontend/src/App.css`  
  - `.plan-section`, `.plan-grid`, `.plan-card`, `.option-table` などのスタイルを追加し、カードベースで Learning/Action/Self-check をレイアウト。
- `backend/app/jobs/__init__.py`  
  - 04 と同一ロジック（Wantedly/Remotive クロール → LLM or キーワードスコア → 最大 3 回リトライ）を維持しつつ、Planner 表示用に `queries` / `sources` を整形。
- `backend/app/db.py`  
  - `DEFAULT_PROFILE` を Generalist 5 年の WAKE Guest に差し替え、初期状態でもプラン生成が成立するようにしました。

## 代表的なスニペット

### 推薦→求人→プランのステージ制御（`frontend/src/pages/Home.tsx`）

```tsx
const [plannerStage, setPlannerStage] = useState<'idle'|'plan'|'synthesize'|'validate'|'done'|'error'>('idle');
const [planReport, setPlanReport] = useState<PlanReport | null>(null);

const handleRecommend = async () => {
  const recoResponse = await fetchRecommendations(...);
  setRecommendations(recoResponse.recommendations);
  // Planner を発火
  setPlannerStage('plan');
  const report = buildPlanReport(recoResponse.recommendations, readyProfile);
  await sleep(120);
  setPlanReport(report);
  setPlannerStage('done');
};
```

### AgentActivity へのレーン追加（`frontend/src/components/AgentActivity.tsx`）

```tsx
type PlannerStage = 'idle'|'plan'|'synthesize'|'validate'|'done'|'error';

const plannerSteps: Record<PlannerStage, ActivityStep> = {
  plan: { label: 'プランニング', color: 'blue' },
  synthesize: { label: '統合', color: 'blue' },
  validate: { label: '自己検証', color: 'blue' },
  done: { label: '完了', color: 'green' },
  error: { label: '失敗', color: 'red' },
  idle: { label: '待機', color: 'slate' },
};
```

## LangGraph の扱い

- `backend/app/rag/graph.py` の StateGraph (`build_query → retrieve → call_model → respond`) は 04 から変更なし。MODE=fake では `_call_model` がオフライン回答を返すフェイルセーフも据え置きです。
- 05 で追加された Planner はフロントエンド内で完結する決定論的ロジックのため、LangGraph のノードやトポロジーを修正せずに「エージェントがもう 1 体いる」ように見せています。

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
- 面談用プランボードで Learning / Action / Self-check の各カードを自分のプロフィールに合わせて書き換え、`buildPlanReport` のテンプレを編集すると即座に UI が更新されることを体感。
- 04 の UI と比較し、LangGraph+求人ロジックを据え置いたままフロントのみでプランニング層を後付けできる構成を確認。

## 学習ポイント

- **決定論的 Planner でフェイルセーフ**: LLM が不調でも、テンプレベースのプラン生成によって最低限の提案が返せる。
- **三段パイプラインの可視化**: プランニングを含めたステージ管理を UI で見せることで、LangGraph 的なグラフ実行の理解が進む。
- **データ/構成のレバレッジ**: バックエンドは 04 と同等のまま、UI とサンプルデータを工夫するだけでユーザ体験を大きく変えられることを確認できます。
