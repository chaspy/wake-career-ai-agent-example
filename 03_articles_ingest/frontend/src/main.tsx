import React, { useEffect, useMemo, useState } from 'react'
import { createRoot } from 'react-dom/client'
import './style.css'

type ArticleSummary = { slug: string; title: string; source_url: string }
type ArticleDetail = ArticleSummary & { body: string }
type Health = { ok: boolean; phase: string; mode: string; provider: string }
type Recommendation = {
  slug: string
  title: string
  url: string
  score: number
  excerpt: string
  reasons: string[]
  citations: string[]
}
type RecommendResponse = { recommendations: Recommendation[]; mode: string }

function App() {
  const [health, setHealth] = useState<Health | null>(null)
  const [articles, setArticles] = useState<ArticleSummary[]>([])
  const [detail, setDetail] = useState<ArticleDetail | null>(null)
  const [query, setQuery] = useState('キャリア AI')
  const [recs, setRecs] = useState<Recommendation[]>([])
  const [status, setStatus] = useState('')

  const loading = useMemo(() => status.includes('中') || status.includes('loading'), [status])

  useEffect(() => {
    fetch('/api/health').then((r) => r.json()).then(setHealth)
    fetch('/api/articles').then((r) => r.json()).then(setArticles)
  }, [])

  const openArticle = async (slug: string) => {
    setStatus('読み込み中...')
    const res = await fetch(`/api/articles/${slug}`)
    if (!res.ok) {
      setStatus('not found')
      return
    }
    setDetail(await res.json())
    setStatus('')
  }

  const fetchRecs = async () => {
    setStatus('推薦取得中...')
    const res = await fetch('/api/recommendations', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query, top_k: 3 }),
    })
    setStatus('')
    if (!res.ok) {
      setStatus('推薦取得に失敗しました')
      return
    }
    const data: RecommendResponse = await res.json()
    setRecs(data.recommendations)
  }

  return (
    <main className="app-shell">
      <header className="card hero">
        <p className="eyebrow">phase 03 / articles ingest</p>
        <h1>記事の閲覧と RAG 推薦を体験</h1>
        <p className="muted">ベクトルストアへのインジェストと推薦出力を 1 画面で確認します。</p>
        <div className="status-row">
          <span className={`badge ${health ? 'success' : 'neutral'}`}>
            Health: {health ? `${health.phase} (${health.mode})` : '---'}
          </span>
          <span className={`badge ${status ? 'success' : 'neutral'}`}>状態: {status || '待機中'}</span>
        </div>
      </header>

      <section className="grid-three">
        <div className="card">
          <p className="eyebrow small">記事一覧</p>
          <div className="stack">
            {articles.length === 0 ? (
              <p className="muted">まだ記事がありません。</p>
            ) : (
              articles.map((a) => (
                <button key={a.slug} className="link" onClick={() => openArticle(a.slug)}>
                  {a.title}
                </button>
              ))
            )}
          </div>
        </div>

        <div className="card">
          <p className="eyebrow small">本文プレビュー</p>
          {detail ? (
            <article className="stack">
              <div className="space-between">
                <h3>{detail.title}</h3>
                <span className="pill">{detail.slug}</span>
              </div>
              <p className="muted">{detail.source_url}</p>
              <pre>{detail.body}</pre>
            </article>
          ) : (
            <p className="muted">記事を選択してください。</p>
          )}
        </div>

        <div className="card reco">
          <div className="space-between">
            <p className="eyebrow small">RAG 推薦</p>
            <span className={`badge ${loading ? 'neutral' : 'success'}`}>{loading ? '処理中' : '待機中'}</span>
          </div>
          <label>
            クエリ
            <input value={query} onChange={(e) => setQuery(e.target.value)} />
          </label>
          <button onClick={fetchRecs} disabled={loading}>
            {loading ? '取得中...' : 'おすすめを取得'}
          </button>
          <div className="stack">
            {recs.length === 0 ? (
              <p className="muted">まだ推薦はありません</p>
            ) : (
              recs.map((r) => (
                <article key={r.slug} className="card" style={{ padding: '1rem' }}>
                  <div className="space-between">
                    <h3>{r.title}</h3>
                    <span className="score">{r.score.toFixed(2)}</span>
                  </div>
                  <p className="muted">{r.url}</p>
                  <p>{r.excerpt}</p>
                  <ul>
                    {r.reasons.map((reason, idx) => (
                      <li key={idx}>{reason}</li>
                    ))}
                  </ul>
                </article>
              ))
            )}
          </div>
        </div>
      </section>
    </main>
  )
}

createRoot(document.getElementById('root')!).render(<App />)
