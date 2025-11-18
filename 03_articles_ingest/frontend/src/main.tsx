import React, { useEffect, useState } from 'react'
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

  useEffect(() => {
    fetch('/api/health').then((r) => r.json()).then(setHealth)
    fetch('/api/articles').then((r) => r.json()).then(setArticles)
  }, [])

  const openArticle = async (slug: string) => {
    setStatus('loading...')
    const res = await fetch(`/api/articles/${slug}`)
    if (!res.ok) {
      setStatus('not found')
      return
    }
    setDetail(await res.json())
    setStatus('')
  }

  return (
    <main className="shell">
      <h1>03_articles_ingest</h1>
      <p className="muted">
        Health: {health ? `${health.phase} (${health.mode})` : '...'} {status}
      </p>
      <div className="grid">
        <section>
          <h2>記事一覧</h2>
          <ul>
            {articles.map((a) => (
              <li key={a.slug}>
                <button className="link" onClick={() => openArticle(a.slug)}>
                  {a.title}
                </button>
              </li>
            ))}
          </ul>
        </section>
        <section>
          <h2>詳細</h2>
          {detail ? (
            <article>
              <h3>{detail.title}</h3>
              <p className="muted">{detail.source_url}</p>
              <pre>{detail.body}</pre>
            </article>
          ) : (
            <p className="muted">記事を選択してください</p>
          )}
        </section>
        <section>
          <h2>おすすめ（RAG）</h2>
          <div className="stack gap-sm">
            <label>
              クエリ
              <input value={query} onChange={(e) => setQuery(e.target.value)} />
            </label>
            <button
              onClick={async () => {
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
              }}
            >
              おすすめを取得
            </button>
            <div className="stack">
              {recs.length === 0 ? (
                <p className="muted">まだ推薦はありません</p>
              ) : (
                recs.map((r) => (
                  <article key={r.slug} className="card">
                    <div className="space-between">
                      <h3>{r.title}</h3>
                      <span className="muted">score {r.score.toFixed(2)}</span>
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
      </div>
    </main>
  )
}

createRoot(document.getElementById('root')!).render(<App />)
