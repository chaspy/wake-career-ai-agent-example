import React, { useMemo, useState } from 'react'
import { createRoot } from 'react-dom/client'
import './style.css'

function App() {
  const [prompt, setPrompt] = useState('こんにちは、今日は何をすべき？')
  const [reply, setReply] = useState('')
  const [mode, setMode] = useState('')
  const [status, setStatus] = useState('')

  const loading = useMemo(() => status.startsWith('送信中'), [status])

  const handlePing = async () => {
    setStatus('送信中...')
    try {
      const res = await fetch('/api/ping-llm', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt }),
      })
      if (!res.ok) throw new Error(await res.text())
      const data = await res.json()
      setReply(data.reply)
      setMode(data.mode)
      setStatus('完了')
    } catch (e: any) {
      setStatus(`失敗: ${e.message}`)
    }
  }

  return (
    <main className="app-shell">
      <header className="card hero">
        <p className="eyebrow">phase 01 / bootstrap</p>
        <h1>バックエンドと LLM 呼び出しの疎通を確認</h1>
        <p className="muted">最小プロンプト → LLM 応答だけに絞ったステップです。</p>
        <div className="status-row">
          <span className={`badge ${status ? 'success' : 'neutral'}`}>状態: {status || '待機中'}</span>
          <span className={`badge ${mode === 'live' ? 'live' : 'neutral'}`}>MODE: {mode || '---'}</span>
        </div>
      </header>

      <section className="grid-two">
        <div className="card">
          <label>
            プロンプト
            <textarea value={prompt} onChange={(e) => setPrompt(e.target.value)} />
          </label>
          <button onClick={handlePing} disabled={loading}>
            {loading ? '送信中...' : 'LLM に送る'}
          </button>
        </div>

        <div className="card reply-card">
          <p className="eyebrow small">LLM 応答</p>
          <p className="helper">改行や日本語をそのまま確認できます。</p>
          <pre className="reply-box">{reply || 'まだ返信はありません。'}</pre>
        </div>
      </section>
    </main>
  )
}

createRoot(document.getElementById('root')!).render(<App />)
