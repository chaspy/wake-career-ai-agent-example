import React, { useState, useEffect, useMemo } from 'react'
import { createRoot } from 'react-dom/client'
import './style.css'

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

type Health = { ok: boolean; phase: string }

async function fetchHealth(): Promise<Health> {
  const res = await fetch(apiUrl('/api/health'))
  if (!res.ok) throw new Error('health failed')
  return res.json()
}

async function fetchProfile(): Promise<ProfileResponse | null> {
  const res = await fetch(apiUrl('/api/profile'))
  if (res.status === 404) return null
  if (!res.ok) throw new Error('profile failed')
  return res.json()
}

async function saveProfile(data: Profile): Promise<ProfileResponse> {
  const res = await fetch(apiUrl('/api/profile'), {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })
  if (!res.ok) throw new Error('save failed')
  return res.json()
}

const API_BASE = import.meta.env.VITE_API_BASE || ''

function apiUrl(path: string) {
  if (!API_BASE) return path
  return `${API_BASE.replace(/\/$/, '')}${path}`
}

async function askAdvice(question: string): Promise<AdviceResponse> {
  const res = await fetch(apiUrl('/api/profile/advice'), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question }),
  })
  if (res.status === 404) throw new Error('プロフィールを保存してから試してください')
  if (!res.ok) throw new Error('advice failed')
  return res.json()
}

function App() {
  const [health, setHealth] = useState<Health | null>(null)
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
  const [status, setStatus] = useState('')
  const [question, setQuestion] = useState('次に身につけた方が良いスキルは？')
  const [advice, setAdvice] = useState<AdviceResponse | null>(null)

  const saving = useMemo(() => status.startsWith('保存'), [status])
  const calling = useMemo(() => status.startsWith('LLM'), [status])

  useEffect(() => {
    fetchHealth().then(setHealth)
    fetchProfile().then((p) => p && setProfile(p))
  }, [])

  useEffect(() => {
    if (profile) setForm(profile)
  }, [profile])

  const update = (key: keyof Profile, value: any) => {
    setForm((f) => ({ ...f, [key]: value }))
  }

  return (
    <main className="app-shell">
      <header className="card hero">
        <p className="eyebrow">phase 02 / profile api</p>
        <h1>プロフィールの保存と LLM 相談</h1>
        <p className="muted">保存したプロフィールを使ってキャリア相談できる状態にします。</p>
        <div className="status-row">
          <span className={`badge ${health ? 'success' : 'neutral'}`}>
            Health: {health ? `${health.phase} OK` : '---'}
          </span>
          <span className={`badge ${status ? 'success' : 'neutral'}`}>状態: {status || '待機中'}</span>
        </div>
      </header>

      <section className="grid-two">
        <div className="card">
          <p className="eyebrow small">プロフィール</p>
          <label>
            氏名
            <input value={form.name} onChange={(e) => update('name', e.target.value)} />
          </label>
          <label>
            経験年数
            <input type="number" value={form.years} onChange={(e) => update('years', Number(e.target.value))} />
          </label>
          <label>
            現在の役割
            <input value={form.current_role} onChange={(e) => update('current_role', e.target.value)} />
          </label>
          <label>
            目標の役割
            <input value={form.target_role} onChange={(e) => update('target_role', e.target.value)} />
          </label>
          <label>
            スキル（カンマ区切り）
            <input
              className="tag-input"
              value={form.skills.join(', ')}
              onChange={(e) => update('skills', e.target.value.split(',').map((v) => v.trim()).filter(Boolean))}
            />
          </label>
          <label>
            興味（カンマ区切り）
            <input
              className="tag-input"
              value={form.interests.join(', ')}
              onChange={(e) => update('interests', e.target.value.split(',').map((v) => v.trim()).filter(Boolean))}
            />
          </label>
          <label>
            ノート
            <textarea value={form.notes ?? ''} onChange={(e) => update('notes', e.target.value)} />
          </label>

          <div className="actions">
            <button
              onClick={async () => {
                try {
                  setStatus('保存中...')
                  const saved = await saveProfile(form)
                  setProfile(saved)
                  setStatus('保存しました')
                } catch (e: any) {
                  setStatus(`失敗: ${e.message}`)
                }
              }}
              disabled={saving}
            >
              {saving ? '保存中...' : '保存'}
            </button>
            <button onClick={() => profile && setForm(profile)} className="ghost" disabled={!profile}>
              取り消し
            </button>
          </div>
        </div>

        <div className="card reply">
          <p className="eyebrow small">LLM にキャリア相談</p>
          <p className="muted">保存済みプロフィールを自動でプロンプトに入れます。</p>
          <label>
            質問
            <input value={question} onChange={(e) => setQuestion(e.target.value)} />
          </label>
          <div className="actions">
            <button
              onClick={async () => {
                try {
                  setStatus('LLM 呼び出し中...')
                  const res = await askAdvice(question)
                  setAdvice(res)
                  setStatus(`回答取得 (${res.provider})`)
                } catch (e: any) {
                  setStatus(`失敗: ${e.message}`)
                }
              }}
              disabled={calling}
            >
              {calling ? '呼び出し中...' : 'アドバイスをもらう'}
            </button>
          </div>
          {advice ? (
            <div className="info-strip">
              <span className="muted">provider: {advice.provider}</span>
            </div>
          ) : (
            <p className="muted">保存後に質問すると回答がここに出ます。</p>
          )}
          <pre>{advice?.answer ?? '回答待ち…'}</pre>
        </div>
      </section>
    </main>
  )
}

createRoot(document.getElementById('root')!).render(<App />)
