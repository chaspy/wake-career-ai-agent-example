import React, { useState, useEffect } from 'react'
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

type Health = { ok: boolean; phase: string }

async function fetchHealth(): Promise<Health> {
  const res = await fetch('/api/health')
  if (!res.ok) throw new Error('health failed')
  return res.json()
}

async function fetchProfile(): Promise<ProfileResponse | null> {
  const res = await fetch('/api/profile')
  if (res.status === 404) return null
  if (!res.ok) throw new Error('profile failed')
  return res.json()
}

async function saveProfile(data: Profile): Promise<ProfileResponse> {
  const res = await fetch('/api/profile', {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })
  if (!res.ok) throw new Error('save failed')
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
    <main className="shell">
      <h1>02_profile_api</h1>
      <p className="muted">Health: {health ? `${health.phase} OK` : '...'} / 状態: {status}</p>

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
          value={form.skills.join(', ')}
          onChange={(e) => update('skills', e.target.value.split(',').map((v) => v.trim()).filter(Boolean)))}
        />
      </label>
      <label>
        興味（カンマ区切り）
        <input
          value={form.interests.join(', ')}
          onChange={(e) => update('interests', e.target.value.split(',').map((v) => v.trim()).filter(Boolean)))}
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
        >
          保存
        </button>
        <button onClick={() => profile && setForm(profile)} className="ghost">
          取り消し
        </button>
      </div>
    </main>
  )
}

createRoot(document.getElementById('root')!).render(<App />)
