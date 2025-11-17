import type { HealthResponse } from '../lib/types'

interface ApiKeyBannerProps {
  health: HealthResponse | null
}

export function ApiKeyBanner({ health }: ApiKeyBannerProps) {
  const mode = health?.mode ?? 'fake'
  const provider = health?.provider ?? (mode === 'live' ? 'OpenAI' : 'fake')
  return (
    <div className="api-key-banner" role="status">
      <div>
        <strong>MODE:</strong> {mode} {provider ? `· Provider: ${provider}` : ''}
      </div>
      <span className="muted">
        {mode === 'fake'
          ? 'APIキーなしのローカル推論モードです。OpenAIキーを .envrc で設定すると live に切り替えられます。'
          : `Provider=${provider} の live モードです。引用付きで理由が生成されます。`}
      </span>
    </div>
  )
}
