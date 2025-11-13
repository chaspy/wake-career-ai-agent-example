import { useEffect, useMemo, useState } from 'react'
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
  listArticles,
  saveProfile,
} from '../lib/api'
import type {
  ArticleDetail as ArticleDetailType,
  ArticleSummary,
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
  const [articles, setArticles] = useState<ArticleSummary[]>([])

  const [activeArticle, setActiveArticle] = useState<ArticleDetailType | null>(null)
  const [articleLoading, setArticleLoading] = useState(false)
  const [articleError, setArticleError] = useState<string | null>(null)

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

  useEffect(() => {
    listArticles()
      .then((list) => setArticles(list))
      .catch(() => undefined)
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

  const handleRecommend = async () => {
    setRecoLoading(true)
    setRecoError(null)
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
      <section className="hero-grid">
        <div className="card">
          <h1>WAKE Career RAG Recommender</h1>
          <p className="tagline">プロフィールとクエリから WAKE 記事を引用付きでレコメンド</p>
          <ApiKeyBanner health={health} />
          <div className="status-block">
            <span className="label">API health</span>
            {health ? (
              <span className="status ok">{health.mode} mode ready</span>
            ) : healthError ? (
              <span className="status error">{healthError}</span>
            ) : (
              <span className="status info">checking…</span>
            )}
          </div>
          <div className="actions-row">
            <label>
              <span>追加の検索キーワード</span>
              <input
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="AI PM, 1on1, ハイブリッドワークなど"
              />
            </label>
            <button className="primary" onClick={handleRecommend} disabled={recoLoading}>
              {recoLoading ? '取得中…' : 'おすすめを取得'}
            </button>
          </div>
          {recoError && <p className="status error">{recoError}</p>}
        </div>
        <div className="card">
          <h2>最新の WAKE 記事</h2>
          {articles.length === 0 ? (
            <p className="muted">seed スクリプトで記事を登録するとここに表示されます。</p>
          ) : (
            <ul>
              {articles.slice(0, 5).map((article) => (
                <li key={article.slug}>
                  <button className="ghost" onClick={() => handleOpenArticle(article.slug)}>
                    {article.title}
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
      </section>

      <section className="card">
        {profileLoading ? <Loader /> : null}
        <ProfileForm
          key={profile?.updated_at ?? profile?.name ?? 'empty-profile'}
          profile={profile}
          onSave={handleSaveProfile}
          saving={savingProfile}
        />
      </section>

      <section className="card">
        <h2>おすすめ記事</h2>
        {recoLoading && <Loader />}
        <RecoList items={recommendations} onOpenArticle={handleOpenArticle} />
      </section>

      {articleLoading && !activeArticle && <Loader />}
      {articleError && <p className="status error">{articleError}</p>}
      {activeArticle && <ArticleDetail article={activeArticle} onClose={() => setActiveArticle(null)} />}
    </main>
  )
}
