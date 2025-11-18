import React, { useEffect, useState } from 'react'
import { createRoot } from 'react-dom/client'
import './style.css'

type ArticleSummary = { slug: string; title: string; source_url: string }
type ArticleDetail = ArticleSummary & { body: string }
type Recommendation = { slug: string; title: string; url: string; score: number; excerpt: string; reasons: string[]; citations: string[] }
type RecommendationResponse = { recommendations: Recommendation[]; mode: string }
type Job = { id: string; title: string; company: string; location: string; url: string; snippet: string }
type JobResponse = { jobs: Job[]; sources: string[]; queries: string[] }

type Health = { ok: boolean; phase: string; mode: string; provider: string }

function App() {
  const [health, setHealth] = useState<Health | null>(null)
  const [articles, setArticles] = useState<ArticleSummary[]>([])
  const [detail, setDetail] = useState<ArticleDetail | null>(null)
  const [recs, setRecs] = useState<Recommendation[]>([])
  const [query, setQuery] = useState('AI キャリア')
  const [jobs, setJobs] = useState<Job[]>([])
  const [jobQuery, setJobQuery] = useState('AI')
  const [status, setStatus] = useState('')

  useEffect(() => {
    fetch('/api/health').then((r) => r.json()).then(setHealth)
    fetch('/api/articles').then((r) => r.json()).then(setArticles)
  }, [])

  const recommend = async () => {
    setStatus('RAG 推薦取得中...')
    const res = await fetch('/api/recommendations', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query, top_k: 3 }),
    })
    const data: RecommendationResponse = await res.json()
    setRecs(data.recommendations)
    setStatus('')
  }

  const searchJobs = async () => {
    setStatus('求人検索中...')
    const res = await fetch('/api/jobs/search', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query: jobQuery, limit: 5 }),
    })
    const data: JobResponse = await res.json()
    setJobs(data.jobs)
    setStatus('')
  }

  const open = async (slug: string) => {
    const res = await fetch(`/api/articles/${slug}`)
    setDetail(await res.json())
  }

  return (
    <main className="shell">
      <h1>04_recommend_rag</h1>
      <p className="muted">Health: {health ? `${health.phase} (${health.mode})` : '...'} {status}</p>
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
          <label className="stack gap-sm">
            クエリ
            <input value={query} onChange={(e) => setQuery(e.target.value)} />
            <button onClick={recommend}>おすすめを取得</button>
          </label>
          {recs.map((r) => (
            <article key={r.slug} className="card">
              <header className="space-between">
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
        <div>
          <h2>求人検索</h2>
          <label className="stack gap-sm">
            キーワード
            <input value={jobQuery} onChange={(e) => setJobQuery(e.target.value)} />
            <button onClick={searchJobs}>求人を探す（fake）</button>
          </label>
          <div className="stack">
            {jobs.length === 0 ? (
              <p className="muted">まだ求人はありません</p>
            ) : (
              jobs.map((j) => (
                <article key={j.id} className="card">
                  <div className="space-between">
                    <h3>{j.title}</h3>
                    <span className="muted">{j.company}</span>
                  </div>
                  <p className="muted">{j.location}</p>
                  <p>{j.snippet}</p>
                  <a className="link" href={j.url} target="_blank" rel="noreferrer">
                    詳細を見る
                  </a>
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
