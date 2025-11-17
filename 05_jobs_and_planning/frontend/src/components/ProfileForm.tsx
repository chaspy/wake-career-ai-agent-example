import { useState } from 'react'
import type { FormEvent } from 'react'
import type { Profile, ProfileResponse } from '../lib/types'
import './ProfileForm.css'

interface ProfileFormProps {
  profile: ProfileResponse | null
  onSave: (profile: Profile) => Promise<void>
  saving: boolean
}

const emptyProfile: Profile = {
  name: '',
  years: 0,
  current_role: '',
  target_role: '',
  skills: [],
  interests: [],
  notes: '',
}

export function ProfileForm({ profile, onSave, saving }: ProfileFormProps) {
  const [draft, setDraft] = useState<Profile>(() => (profile ? { ...profile, notes: profile.notes ?? '' } : emptyProfile))
  const [skillsInput, setSkillsInput] = useState(() => (profile ? profile.skills.join(', ') : ''))
  const [interestsInput, setInterestsInput] = useState(() => (profile ? profile.interests.join(', ') : ''))
  const [error, setError] = useState<string | null>(null)
  const [savedAt, setSavedAt] = useState<string | null>(profile?.updated_at ?? null)

  const handleChange = (field: keyof Profile) => (event: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const value = field === 'years' ? Number(event.target.value) : event.target.value
    setDraft((prev) => ({ ...prev, [field]: value }))
  }

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault()
    setError(null)
    const payload: Profile = {
      ...draft,
      years: Number.isNaN(draft.years) ? 0 : draft.years,
      skills: splitTags(skillsInput),
      interests: splitTags(interestsInput),
      notes: draft.notes?.trim() || undefined,
    }

    try {
      await onSave(payload)
      setSavedAt(new Date().toISOString())
    } catch (err) {
      setError(err instanceof Error ? err.message : 'プロフィール保存に失敗しました')
    }
  }

  return (
    <form className="profile-form" onSubmit={handleSubmit}>
      <div className="form-header">
        <div>
          <h3>プロフィール設定</h3>
          <p className="form-caption">現在のキャリアと目標を入力すると推薦の精度が上がります。</p>
        </div>
        {savedAt && <span className="muted">最終更新: {new Date(savedAt).toLocaleString()}</span>}
      </div>
      <div className="form-grid">
        <label>
          <span>氏名</span>
          <input value={draft.name} onChange={handleChange('name')} placeholder="WAKE 太郎" required />
        </label>
        <label>
          <span>経験年数</span>
          <input type="number" min={0} value={draft.years} onChange={handleChange('years')} required />
        </label>
        <label>
          <span>現在の役割</span>
          <input value={draft.current_role} onChange={handleChange('current_role')} placeholder="Frontend Engineer" required />
        </label>
        <label>
          <span>目指す役割</span>
          <input value={draft.target_role} onChange={handleChange('target_role')} placeholder="AI Product Manager" required />
        </label>
        <label className="full-width">
          <span>得意スキル（カンマ区切り）</span>
          <input value={skillsInput} onChange={(e) => setSkillsInput(e.target.value)} placeholder="React, Python, Facilitation" />
        </label>
        <label className="full-width">
          <span>興味領域（カンマ区切り）</span>
          <input value={interestsInput} onChange={(e) => setInterestsInput(e.target.value)} placeholder="AI教育, 1on1, メンタリング" />
        </label>
        <label className="full-width">
          <span>メモ</span>
          <textarea value={draft.notes ?? ''} onChange={handleChange('notes')} rows={3} placeholder="学びたいことや制約条件など" />
        </label>
      </div>
      {error && <p className="form-error">{error}</p>}
      <button type="submit" className="primary" disabled={saving}>
        {saving ? '保存中…' : 'プロフィールを保存'}
      </button>
    </form>
  )
}

function splitTags(value: string): string[] {
  return value
    .split(',')
    .map((item) => item.trim())
    .filter(Boolean)
}
