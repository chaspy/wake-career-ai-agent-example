import React, { useState } from 'react'
import { createRoot } from 'react-dom/client'
import './style.css'

function App() {
  const [prompt, setPrompt] = useState('こんにちは、今日は何をすべき？')
  const [reply, setReply] = useState('')
  const [mode, setMode] = useState('')
  const [status, setStatus] = useState('')

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
    <main className="shell">
      <h1>01_bootstrap</h1>
      <p>バックエンドと LLM 呼び出しが通るか最小確認するフェーズです。</p>
      <label>
        プロンプト
        <textarea value={prompt} onChange={(e) => setPrompt(e.target.value)} />
      </label>
      <button onClick={handlePing}>LLM に送る</button>
      <p className="muted">状態: {status} / MODE: {mode || '---'}</p>
      <pre className="reply">{reply}</pre>
    </main>
  )
}

createRoot(document.getElementById('root')!).render(<App />)
