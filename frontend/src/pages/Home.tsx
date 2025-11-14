import { useEffect, useMemo, useRef, useState } from 'react'
import { ApiKeyBanner } from '../components/ApiKeyBanner'
import { ArticleDetail } from '../components/ArticleDetail'
import { Loader } from '../components/Loader'
import { ProfileForm } from '../components/ProfileForm'
import { RecoList } from '../components/RecoList'
import {
  fetchArticle,
  fetchHealth,
  fetchProfile,
  fetchRecommendations,
  saveProfile,
} from '../lib/api'
import type {
  ArticleDetail as ArticleDetailType,
  HealthResponse,
  Profile,
  ProfileResponse,
  Recommendation,
} from '../lib/types'

export function Home() {
  const [health, setHealth] = useState<HealthResponse | null>(null)
  const [healthError, setHealthError] = useState<string | null>(null)

  const [profile, setProfile] = useState<ProfileResponse | null>(null)
  const [profileLoading, setProfileLoading] = useState(true)
  const [savingProfile, setSavingProfile] = useState(false)

  const [recommendations, setRecommendations] = useState<Recommendation[]>([])
  const [recoLoading, setRecoLoading] = useState(false)
  const [recoError, setRecoError] = useState<string | null>(null)

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

  const handleRecommend = async () => {
    setRecoLoading(true)
    setRecoError(null)
    scrollToRecommendations()
    try {
      const response = await fetchRecommendations({
        profile: readyProfile ?? undefined,
        query: query || undefined,
        top_k: 3,
      })
      setRecommendations(response.recommendations)
      setHealth({ ok: true, mode: response.mode })
    } catch (err) {
      setRecoError(err instanceof Error ? err.message : '推薦の取得に失敗しました')
    } finally {
      setRecoLoading(false)
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

      <section className="card reco-section" ref={recoSectionRef}>
        <div className="reco-header">
          <h2>おすすめ記事</h2>
          <p className="muted">提案されたカードから記事を開き、引用元を確認できます。</p>
        </div>
        {recoLoading && <Loader />}
        <RecoList items={recommendations} onOpenArticle={handleOpenArticle} />
      </section>

      {articleLoading && !activeArticle && <Loader />}
      {articleError && <p className="status error">{articleError}</p>}
      {activeArticle && <ArticleDetail article={activeArticle} onClose={() => setActiveArticle(null)} />}
    </main>
  )
}
