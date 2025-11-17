import React, { useEffect, useState } from 'react'
import { createRoot } from 'react-dom/client'
import './style.css'

type ArticleSummary = { slug: string; title: string; source_url: string }
type ArticleDetail = ArticleSummary & { body: string }
type Health = { ok: boolean; phase: string }

function App() {
  const [health, setHealth] = useState<Health | null>(null)
  const [articles, setArticles] = useState<ArticleSummary[]>([])
  const [detail, setDetail] = useState<ArticleDetail | null>(null)
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
      <p className="muted">Health: {health ? `${health.phase} OK` : '...'} {status}</p>
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
      </div>
    </main>
  )
}

createRoot(document.getElementById('root')!).render(<App />)
