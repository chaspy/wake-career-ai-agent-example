import type { HealthResponse } from '../lib/types'

interface ApiKeyBannerProps {
  health: HealthResponse | null
}

export function ApiKeyBanner({ health }: ApiKeyBannerProps) {
  const mode = health?.mode ?? 'fake'
  return (
    <div className="api-key-banner" role="status">
      <div>
        <strong>MODE:</strong> {mode}
      </div>
      <span className="muted">
        {mode === 'fake'
          ? 'APIキーなしのローカル推論モードです。OpenAIキーを .envrc で設定すると live に切り替えられます。'
          : 'OpenAI API を利用した live モードです。引用付きで理由が生成されます。'}
      </span>
    </div>
  )
}
