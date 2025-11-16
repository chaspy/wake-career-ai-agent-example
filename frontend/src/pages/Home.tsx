import { useEffect, useMemo, useRef, useState } from 'react'
import { ApiKeyBanner } from '../components/ApiKeyBanner'
import { ArticleDetail } from '../components/ArticleDetail'
import { JobList } from '../components/JobList'
import { Loader } from '../components/Loader'
import { ProfileForm } from '../components/ProfileForm'
import { RecoList } from '../components/RecoList'
import { AgentActivity } from '../components/AgentActivity'
import {
  fetchArticle,
  fetchHealth,
  fetchProfile,
  fetchRecommendations,
  saveProfile,
  searchJobs,
} from '../lib/api'
import type {
  ArticleDetail as ArticleDetailType,
  HealthResponse,
  JobSearchResponse,
  JobSummary,
  Profile,
  ProfileResponse,
  Recommendation,
} from '../lib/types'

type PlanReport = {
  profileInsights: string[]
  careerOptions: { title: string; rationale: string; citation?: string; distance: string; risk: string; next: string }[]
  learning: string[]
  actions: string[]
  selfCheck: string[]
}

export function Home() {
  const [health, setHealth] = useState<HealthResponse | null>(null)
  const [healthError, setHealthError] = useState<string | null>(null)

  const [profile, setProfile] = useState<ProfileResponse | null>(null)
  const [profileLoading, setProfileLoading] = useState(true)
  const [savingProfile, setSavingProfile] = useState(false)

  const [recommendations, setRecommendations] = useState<Recommendation[]>([])
  const [recoLoading, setRecoLoading] = useState(false)
  const [recoError, setRecoError] = useState<string | null>(null)
  const [recoStage, setRecoStage] = useState<'idle' | 'plan' | 'crawl' | 'rank' | 'done' | 'error'>('idle')
  const [plannerStage, setPlannerStage] = useState<'idle' | 'plan' | 'synthesize' | 'validate' | 'done' | 'error'>('idle')
  const [plannerError, setPlannerError] = useState<string | null>(null)

  const [jobs, setJobs] = useState<JobSummary[]>([])
  const [jobsLoading, setJobsLoading] = useState(false)
  const [jobsError, setJobsError] = useState<string | null>(null)
  const [jobSources, setJobSources] = useState<string[]>([])
  const [jobQueries, setJobQueries] = useState<string[]>([])
  const [jobStage, setJobStage] = useState<'idle' | 'plan' | 'crawl' | 'rank' | 'done' | 'error'>('idle')
  const [planReport, setPlanReport] = useState<PlanReport | null>(null)

  const [query, setQuery] = useState('')
  const [activeArticle, setActiveArticle] = useState<ArticleDetailType | null>(null)
  const [articleLoading, setArticleLoading] = useState(false)
const [articleError, setArticleError] = useState<string | null>(null)
  const recoSectionRef = useRef<HTMLElement | null>(null)

  useEffect(() => {
    const controller = new AbortController()
    fetchHealth(controller.signal)
      .then((data) => {
        setHealth(data)
        setHealthError(null)
      })
      .catch((error) => {
        if (error.name === 'AbortError') return
        setHealthError(error instanceof Error ? error.message : 'health check failed')
      })
    return () => controller.abort()
  }, [])

  useEffect(() => {
    fetchProfile()
      .then((data) => setProfile(data))
      .finally(() => setProfileLoading(false))
  }, [])

  const readyProfile: Profile | null = useMemo(() => {
    if (!profile) return null
    return {
      name: profile.name,
      years: profile.years,
      current_role: profile.current_role,
      target_role: profile.target_role,
      skills: profile.skills,
      interests: profile.interests,
      notes: profile.notes,
    }
  }, [profile])

  const handleSaveProfile = async (data: Profile) => {
    setSavingProfile(true)
    try {
      const saved = await saveProfile(data)
      setProfile(saved)
    } finally {
      setSavingProfile(false)
    }
  }

  const scrollToRecommendations = () => {
    if (recoSectionRef.current) {
      recoSectionRef.current.scrollIntoView({ behavior: 'smooth', block: 'start' })
    }
  }

  const sleep = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms))

  const buildPlanReport = (recs: Recommendation[], profile: Profile | null): PlanReport => {
    const profileInsights = [
      `あなたは「${profile?.current_role ?? '未入力'}」として ${profile?.years ?? 0} 年の経験を持ち、目標は「${profile?.target_role ?? '未入力'}」。`,
      `主力スキルは ${(profile?.skills ?? []).join(' / ') || '（未入力）'}、興味は ${(profile?.interests ?? []).join(' / ') || '（未入力）'}。`,
      'これらを踏まえ、次の3つの進路オプションと短期プランを提示します。',
    ]

    const firstRec = recs[0]
    const secondRec = recs[1]
    const firstThreeRecs = recs.slice(0, 3)
    const careerOptions = [
      {
        title: 'オプション1: SRE/プラットフォームを極めてリードロールへ',
        rationale:
          '現職スキルを軸に信頼できる成果を積み上げ、短期でテックリード・EMに昇格するルート。信頼性・生産性指標を改善する実績が鍵。',
        citation: firstRec?.citations?.[0]?.source_url,
        distance: '短',
        risk: '低',
        next: '直近3ヶ月でSLO改善と自動化成果をまとめ、社内外で共有する',
      },
      {
        title: 'オプション2: EM/CTO候補として組織スケールに軸足を移す',
        rationale:
          'マネジメントと技術意思決定を両立し、1→10/10→100フェーズの組織設計を経験するルート。採用・評価・技術負債返済の設計が必須。',
        citation: secondRec?.citations?.[0]?.source_url,
        distance: '中',
        risk: '中',
        next: 'チームヘルス指標と技術負債の棚卸しを行い、90日改善ロードマップを提示する',
      },
      {
        title: 'オプション3: AIプロダクト／MLOpsへピボットして市場価値を上げる',
        rationale:
          '既存のSRE/インフラ経験をAI基盤・MLOpsに接続し、生成AIプロダクトの信頼性/コスト最適化を担うルート。新領域だが需要成長率が高い。',
        citation: recs[2]?.citations?.[0]?.source_url,
        distance: '中〜長',
        risk: '中',
        next: '社内PoCかOSSで小規模なLLM推論基盤を構築し、コストとSLOを計測したレポートを作成する',
      },
    ]

    const learning = [
      firstThreeRecs[0]
        ? `「${firstThreeRecs[0].title}」を読み、引用部分と学びを3項目メモ（URL: ${firstThreeRecs[0].url})`
        : '推薦された記事を1本選び、引用と学びを3項目メモ',
      firstThreeRecs[1]
        ? `「${firstThreeRecs[1].title}」で対比し、類似/相違を1枚のスライドに整理`
        : '比較用の記事をもう1本選び、違いを1枚に整理',
      '週1回アウトプット（社内ナレッジ/ブログ/デモ）で学びを可視化',
    ]

    const actions = [
      profile?.skills?.[0]
        ? `${profile.skills[0]} を用いたミニプロジェクトを2週間でリリース（GitHub + READMEで学びを書く）`
        : '主力スキルでミニプロジェクトを2週間以内にリリース',
      '推薦記事の引用を使って「過去-現在-未来」の3分ピッチ原稿を作成し録音でセルフレビュー',
      '求人要件から不足スキルを3つ抽出し、カレンダーに学習ブロックを配置',
    ]

    const selfCheck = [
      '1週目: 推薦記事1本の引用メモと3分ピッチ下書きができたか？',
      '2週目: ミニプロジェクトを公開し、READMEに学びを書いたか？',
      '4週目: 受けたい求人2社を決め、職務経歴書をそれに合わせて更新したか？',
    ]

    return { profileInsights, careerOptions, learning, actions, selfCheck }
  }

  const handleRecommend = async () => {
    setRecoLoading(true)
    setRecoError(null)
    setJobsLoading(true)
    setJobsError(null)
    setJobStage('plan')
    setRecoStage('plan')
    setPlannerStage('idle')
    setPlannerError(null)
    setPlanReport(null)
    const seedQuery = (query || '').trim() || 'プロフィールベース'
    setJobQueries(seedQuery ? [seedQuery] : [])
    scrollToRecommendations()
    try {
      await sleep(120)
      setRecoStage('crawl')
      setJobStage('crawl')
      let jobResponse: JobSearchResponse
      try {
        jobResponse = await searchJobs({ profile: readyProfile ?? undefined, query: query || undefined, limit: 10 })
        await sleep(120)
        setJobStage('rank')
      } catch (err) {
        setJobStage('error')
        setJobsError(err instanceof Error ? err.message : '求人取得に失敗しました')
        jobResponse = { jobs: [], sources: [], queries: [] }
      }
      await sleep(120)
      setRecoStage('rank')
      const recoResponse = await fetchRecommendations({
        profile: readyProfile ?? undefined,
        query: query || undefined,
        top_k: 3,
      })
      setRecoStage('done')
      setRecommendations(recoResponse.recommendations)
      setHealth({ ok: true, mode: recoResponse.mode })
      setJobs(jobResponse.jobs)
      setJobSources(jobResponse.sources)
      setJobQueries(jobResponse.queries ?? [])
      if (jobStage !== 'error') {
        setJobStage('done')
      }

      // Planner agent
      setPlannerStage('plan')
      await sleep(80)
      const report = buildPlanReport(recoResponse.recommendations, readyProfile)
      setPlannerStage('synthesize')
      await sleep(120)
      setPlanReport(report)
      setPlannerStage('validate')
      await sleep(120)
      setPlannerStage('done')
    } catch (err) {
      setRecoStage('error')
      setRecoError(err instanceof Error ? err.message : '推薦の取得に失敗しました')
      setPlannerStage('error')
      setPlannerError(err instanceof Error ? err.message : 'プラン生成に失敗しました')
    } finally {
      setRecoLoading(false)
      setJobsLoading(false)
    }
  }

  const handleOpenArticle = async (slug: string) => {
    setArticleLoading(true)
    setArticleError(null)
    try {
      const detail = await fetchArticle(slug)
      setActiveArticle(detail)
    } catch (err) {
      setArticleError(err instanceof Error ? err.message : '記事取得に失敗しました')
    } finally {
      setArticleLoading(false)
    }
  }

  return (
    <main className="app-shell">
      <section className="card profile-card">
        <div className="profile-copy">
          <p className="eyebrow">STEP 1</p>
          <h1>まずはプロフィールを登録しましょう</h1>
          <p className="tagline">現在の役割や興味を登録すると、RAG 推薦があなた仕様になります。</p>
        </div>
        {profileLoading ? <Loader /> : null}
        <ProfileForm
          key={profile?.updated_at ?? profile?.name ?? 'empty-profile'}
          profile={profile}
          onSave={handleSaveProfile}
          saving={savingProfile}
        />
      </section>

      <section className="card cta-card">
        <div className="cta-content">
          <p className="eyebrow">STEP 2</p>
          <h2 className="hero-title">あなたのキャリアにおすすめのコンテンツを生成する！</h2>
          <p className="hero-subtitle">
            保存したプロフィールと追加キーワードをもとに、WAKE Media の記事から引用付きで提案します。
          </p>
          <ApiKeyBanner health={health} />
          <div className="status-block cta-status">
            <span className="label">API health</span>
            {health ? (
              <span className="status ok">{health.mode} mode ready</span>
            ) : healthError ? (
              <span className="status error">{healthError}</span>
            ) : (
              <span className="status info">checking…</span>
            )}
          </div>
          <label className="query-field">
            <span>気になるテーマ（任意）</span>
            <small className="field-hint">
              例: 1on1 / マネジメント転向 / リモートワーク など、絞り込みたいトピックを入れると検索に掛け合わせます
            </small>
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="気になるキーワードを入力（空でもOK）"
            />
          </label>
          <button className="primary hero-button" onClick={handleRecommend} disabled={recoLoading}>
            {recoLoading ? 'おすすめ生成中…' : 'おすすめを取得'}
          </button>
          {recoError && <p className="status error">{recoError}</p>}
        </div>
      </section>

      <AgentActivity
        recoStage={recoStage}
        jobStage={jobStage}
        plannerStage={plannerStage}
        jobQueries={jobQueries}
        jobError={jobsError}
        recoError={recoError}
        plannerError={plannerError}
      />

      <section className="card reco-section" ref={recoSectionRef}>
        <div className="reco-header">
          <h2>おすすめ記事</h2>
          <p className="muted">提案されたカードから記事を開き、引用元を確認できます。</p>
        </div>
        {recoLoading && <Loader />}
        <RecoList items={recommendations} onOpenArticle={handleOpenArticle} />
      </section>

      <section className="card job-section">
        <div className="reco-header">
          <h2>おすすめ求人</h2>
          <p className="muted">公開求人フィード（Wantedly, Remotive など）から自動抽出しています。</p>
        </div>
        {jobsLoading && <Loader />}
        {jobsError && <p className="status error">{jobsError}</p>}
        <JobList
          items={jobs}
          mainSkill={readyProfile?.skills?.[0]}
          targetRole={readyProfile?.target_role}
        />
        {jobSources.length > 0 && <p className="muted">取得元: {jobSources.join(', ')}</p>}
        {jobQueries.length > 0 && <p className="muted">試行クエリ: {jobQueries.join(' → ')}</p>}
      </section>

      {articleLoading && !activeArticle && <Loader />}
      {articleError && <p className="status error">{articleError}</p>}
      {activeArticle && <ArticleDetail article={activeArticle} onClose={() => setActiveArticle(null)} />}

      {planReport && (
        <section className="card plan-section">
          <div className="reco-header">
            <h2>面談用プランボード</h2>
            <p className="muted">エージェントが記事と求人を読んで整理した学習・行動プランと自己検証ポイントです。</p>
          </div>
          <div className="plan-grid">
            <div className="plan-card">
              <p className="eyebrow small">プロファイル分析</p>
              <p className="plan-paragraph">
                {planReport.profileInsights[0]}
                <br />
                {planReport.profileInsights[1]}
                <br />
                {planReport.profileInsights[2]}
              </p>
            </div>

            <div className="plan-card">
              <p className="eyebrow small">キャリア方針の選択肢</p>
              <div className="option-table">
                <div className="option-row head">
                  <span>選択肢</span>
                  <span>距離</span>
                  <span>リスク</span>
                  <span>即できる一手</span>
                </div>
                {planReport.careerOptions.map((opt, idx) => (
                  <div className="option-row" key={`opt-${idx}`}>
                    <div>
                      <strong>{opt.title}</strong>
                      <p className="muted small">{opt.rationale}</p>
                      {opt.citation ? (
                        <a href={opt.citation} target="_blank" rel="noreferrer" className="muted">
                          引用元を見る
                        </a>
                      ) : null}
                    </div>
                    <span>{opt.distance}</span>
                    <span>{opt.risk}</span>
                    <span>{opt.next}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="plan-card">
              <p className="eyebrow small">Learning Plan</p>
              <ul>
                {planReport.learning.map((item, idx) => (
                  <li key={`learn-${idx}`}>{item}</li>
                ))}
              </ul>
            </div>

            <div className="plan-card">
              <p className="eyebrow small">Action Plan (2-4 weeks)</p>
              <ul>
                {planReport.actions.map((item, idx) => (
                  <li key={`act-${idx}`}>{item}</li>
                ))}
              </ul>
            </div>

            <div className="plan-card">
              <p className="eyebrow small">自己検証チェック（Done の定義）</p>
              <ul>
                {planReport.selfCheck.map((item, idx) => (
                  <li key={`self-${idx}`}>{item}</li>
                ))}
              </ul>
            </div>
          </div>
        </section>
      )}
    </main>
  )
}
