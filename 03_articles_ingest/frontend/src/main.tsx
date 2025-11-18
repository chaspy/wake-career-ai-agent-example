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

type Profile = {
  name: string
  years: number
  current_role: string
  target_role: string
  skills: string[]
  interests: string[]
  notes?: string | null
}

type ProfileResponse = Profile
type AdviceResponse = { provider: string; answer: string }

function App() {
  const [health, setHealth] = useState<Health | null>(null)
  const [articles, setArticles] = useState<ArticleSummary[]>([])
  const [query, setQuery] = useState('キャリア AI')
  const [recs, setRecs] = useState<Recommendation[]>([])
  const [status, setStatus] = useState('')

  const [profile, setProfile] = useState<Profile | null>(null)
  const [form, setForm] = useState<Profile>({
    name: '',
    years: 0,
    current_role: '',
    target_role: '',
    skills: [],
    interests: [],
    notes: '',
  })
  const [question, setQuestion] = useState('次に身につけた方が良いスキルは？')
  const [advice, setAdvice] = useState<AdviceResponse | null>(null)
  const [adviceLoading, setAdviceLoading] = useState(false)

  const loading = useMemo(() => status.includes('中') || status.includes('loading'), [status])

  useEffect(() => {
    fetch('/api/health').then((r) => r.json()).then(setHealth)
    fetch('/api/articles').then((r) => r.json()).then(setArticles)
    fetch('/api/profile')
      .then((res) => (res.status === 404 ? null : res.json()))
      .then((data) => data && setProfile(data))
      .catch(() => {})
  }, [])

  useEffect(() => {
    if (profile) setForm(profile)
  }, [profile])

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

  const saveProfile = async () => {
    setStatus('保存中...')
    const res = await fetch('/api/profile', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(form),
    })
    if (!res.ok) {
      setStatus('保存に失敗しました')
      return
    }
    const data: ProfileResponse = await res.json()
    setProfile(data)
    setStatus('保存しました')
  }

  const askAdvice = async () => {
    setAdviceLoading(true)
    setStatus('LLM 呼び出し中...')
    const res = await fetch('/api/profile/advice', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question }),
    })
    if (!res.ok) {
      setStatus('アドバイス取得に失敗しました（プロフィールを保存済みか確認）')
      return
    }
    const data: AdviceResponse = await res.json()
    setAdvice(data)
    setStatus(`回答取得 (${data.provider})`)
    setAdviceLoading(false)
  }

  const updateForm = (key: keyof Profile, value: any) => {
    setForm((prev) => ({ ...prev, [key]: value }))
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

      <section className="card profile-card">
        <div className="panel-header">
          <div>
            <p className="eyebrow small">PROFILE</p>
            <h2>プロフィールを編集</h2>
            <p className="muted">01/02 の続き。保存するとアドバイスと RAG に反映されます。</p>
          </div>
          <div className="actions">
            <button onClick={saveProfile}>保存</button>
            <button className="ghost" onClick={() => profile && setForm(profile)}>
              取り消し
            </button>
          </div>
        </div>
        <div className="profile-grid">
          <label>
            氏名
            <input value={form.name} onChange={(e) => updateForm('name', e.target.value)} />
          </label>
          <label>
            経験年数
            <input type="number" value={form.years} onChange={(e) => updateForm('years', Number(e.target.value))} />
          </label>
          <label>
            現在の役割
            <input value={form.current_role} onChange={(e) => updateForm('current_role', e.target.value)} />
          </label>
          <label>
            目標の役割
            <input value={form.target_role} onChange={(e) => updateForm('target_role', e.target.value)} />
          </label>
          <label className="span2">
            スキル（カンマ区切り）
            <input
              value={form.skills.join(', ')}
              onChange={(e) => updateForm('skills', e.target.value.split(',').map((v) => v.trim()).filter(Boolean))}
            />
          </label>
          <label className="span2">
            興味（カンマ区切り）
            <input
              value={form.interests.join(', ')}
              onChange={(e) => updateForm('interests', e.target.value.split(',').map((v) => v.trim()).filter(Boolean))}
            />
          </label>
          <label className="span2">
            ノート
            <textarea value={form.notes ?? ''} onChange={(e) => updateForm('notes', e.target.value)} />
          </label>
        </div>
      </section>

      <section className="card advice-card">
        <div className="panel-header">
          <div>
            <p className="eyebrow small">LLM ADVICE</p>
            <h2>保存済みプロフィールでキャリア相談</h2>
            <p className="muted">プロフィールをプロンプトに差し込み、fake/OpenAI で回答します。</p>
          </div>
          <div className="actions">
            <button onClick={askAdvice} disabled={adviceLoading}>
              {adviceLoading ? '呼び出し中…' : 'アドバイスをもらう'}
            </button>
          </div>
        </div>
        <label>
          質問
          <input value={question} onChange={(e) => setQuestion(e.target.value)} />
        </label>
        {advice ? (
          <article className="card" style={{ padding: '1rem', background: '#f8fafc' }}>
            <p className="muted">provider: {advice.provider}</p>
            <pre>{advice.answer}</pre>
          </article>
        ) : (
          <p className="muted">{adviceLoading ? 'LLM からの回答を待っています…' : 'まだアドバイスはありません'}</p>
        )}
      </section>

      <section className="card reco full">
        <div className="space-between">
          <div>
            <p className="eyebrow small">RAG 推薦</p>
            <h3>クエリを入れて類似記事を取得</h3>
          </div>
          <span className={`badge ${loading ? 'neutral' : 'success'}`}>{loading ? '処理中' : '待機中'}</span>
        </div>
        <div className="stack">
          <label>
            クエリ
            <input value={query} onChange={(e) => setQuery(e.target.value)} />
          </label>
          <button onClick={fetchRecs} disabled={loading}>
            {loading ? '取得中...' : 'おすすめを取得'}
          </button>
        </div>
        <div className="reco-grid">
          {recs.length === 0 ? (
            <p className="muted">まだ推薦はありません</p>
          ) : (
            recs.map((r) => (
              <article key={r.slug} className="card" style={{ padding: '1rem', width: '100%' }}>
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
      </section>

      <section className="card">
        <div className="space-between">
          <div>
            <p className="eyebrow small">記事一覧</p>
            <h3>ベクトル化済みの記事 100+ 件</h3>
            <p className="muted">クリックで本文を開かず、そのまま RAG 用コンテキストに使います。</p>
          </div>
        </div>
        <ul className="list horizontal">
          {articles.length === 0 ? (
            <p className="muted">まだ記事がありません。</p>
          ) : (
            articles.map((a) => (
              <li key={a.slug}>
                <span className="pill soft">{a.slug}</span>
                <span className="link-text">{a.title}</span>
              </li>
            ))
          )}
        </ul>
      </section>
    </main>
  )
}

createRoot(document.getElementById('root')!).render(<App />)
