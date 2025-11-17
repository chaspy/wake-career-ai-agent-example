import React, { useEffect, useState } from 'react'
import { createRoot } from 'react-dom/client'
import './style.css'

type ArticleSummary = { slug: string; title: string; source_url: string }
type ArticleDetail = ArticleSummary & { body: string }
type Recommendation = { id: string; title: string; url: string; score: number; excerpt: string; reasons: string[]; citations: string[] }
type RecommendationResponse = { recommendations: Recommendation[]; mode: string }

type Health = { ok: boolean; phase: string }

function App() {
  const [health, setHealth] = useState<Health | null>(null)
  const [articles, setArticles] = useState<ArticleSummary[]>([])
  const [detail, setDetail] = useState<ArticleDetail | null>(null)
  const [recs, setRecs] = useState<Recommendation[]>([])

  useEffect(() => {
    fetch('/api/health').then((r) => r.json()).then(setHealth)
    fetch('/api/articles').then((r) => r.json()).then(setArticles)
  }, [])

  const recommend = async () => {
    const res = await fetch('/api/recommendations', { method: 'POST' })
    const data: RecommendationResponse = await res.json()
    setRecs(data.recommendations)
  }

  const open = async (slug: string) => {
    const res = await fetch(`/api/articles/${slug}`)
    setDetail(await res.json())
  }

  return (
    <main className="shell">
      <h1>04_recommend_rag</h1>
      <p className="muted">Health: {health ? `${health.phase} OK` : '...'}</p>
      <button onClick={recommend}>おすすめを取得（ダミー）</button>
      <section className="grid">
        <div>
          <h2>記事一覧</h2>
          <ul>
            {articles.map((a) => (
              <li key={a.slug}>
                <button className="link" onClick={() => open(a.slug)}>
                  {a.title}
                </button>
              </li>
            ))}
          </ul>
        </div>
        <div>
          <h2>おすすめ記事</h2>
          {recs.map((r) => (
            <article key={r.id} className="card">
              <header>
                <h3>{r.title}</h3>
                <span className="score">{r.score.toFixed(2)}</span>
              </header>
              <p className="excerpt">{r.excerpt}</p>
              <ul>
                {r.reasons.map((x, i) => (
                  <li key={i}>{x}</li>
                ))}
              </ul>
            </article>
          ))}
        </div>
        <div>
          <h2>記事詳細</h2>
          {detail ? (
            <article>
              <h3>{detail.title}</h3>
              <p className="muted">{detail.source_url}</p>
              <pre>{detail.body}</pre>
            </article>
          ) : (
            <p className="muted">記事を選択してください</p>
          )}
        </div>
      </section>
    </main>
  )
}

createRoot(document.getElementById('root')!).render(<App />)
