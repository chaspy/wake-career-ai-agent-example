import type { FC } from 'react'

type Props = {
  recoStage: 'idle' | 'plan' | 'crawl' | 'rank' | 'done' | 'error'
  jobStage: 'idle' | 'plan' | 'crawl' | 'rank' | 'done' | 'error'
  jobQueries: string[]
  jobError: string | null
  recoError: string | null
  logs: string[]
  provider?: string | null
}

export const AgentActivity: FC<Props> = ({
  recoStage,
  jobStage,
  jobQueries,
  jobError,
  recoError,
  logs,
  provider,
}) => {
  const statusDot = (state: 'active' | 'error' | 'done' | 'idle') => `dot ${state}`

  const stageToChip = (stage: Props['jobStage'], target: 'plan' | 'crawl' | 'rank') => {
    if (stage === 'error') return 'error'
    if (stage === 'done') return 'done'
    if (stage === target) return 'active'
    if (stage === 'rank' && (target === 'crawl' || target === 'plan')) return 'done'
    if (stage === 'crawl' && target === 'plan') return 'done'
    return 'idle'
  }

  return (
    <section className="card agent-card">
      <div className="agent-header">
        <p className="eyebrow small">AI Agent Activity</p>
        <h3>エージェントの動き</h3>
        <p className="muted">
          推薦と求人探索の進捗をリアルタイム表示します。
          {provider ? ` Provider: ${provider}` : null}
        </p>
      </div>

      <div className="agent-grid">
        <div className="agent-trail">
          <div className="agent-row">
            <span className={statusDot(recoStage === 'error' ? 'error' : recoStage === 'done' ? 'done' : recoStage === 'idle' ? 'idle' : 'active')} />
            <div>
              <p className="agent-label">記事推薦エージェント</p>
              <p className="agent-status">
                {recoStage === 'plan'
                  ? 'プロンプトを組み立て、LangGraph に投入中…'
                  : recoStage === 'crawl'
                    ? 'ベクトル検索と要約を実行中…'
                    : recoStage === 'rank'
                      ? 'スコアリングと引用抽出を整形中…'
                      : recoStage === 'error'
                        ? `エラー: ${recoError}`
                        : recoStage === 'done'
                          ? '完了しました。結果カードに反映しています。'
                          : '待機中。プロフィールとキーワードでいつでも生成できます。'}
              </p>
            </div>
          </div>
        </div>

        <div className="agent-trail">
          <div className="agent-row">
            <span className={statusDot(jobStage === 'error' ? 'error' : jobStage === 'done' ? 'done' : jobStage === 'idle' ? 'idle' : 'active')} />
            <div>
              <p className="agent-label">求人探索エージェント</p>
              <p className="agent-status">
                {jobStage === 'plan'
                  ? 'プロフィールを読み取り、最初のクエリを組み立てています…'
                  : jobStage === 'crawl'
                    ? '外部フィードをクロール中。求人データを収集中…'
                    : jobStage === 'rank'
                      ? 'LLM/キーワードでスコアリングし、必要ならリファイン中…'
                      : jobStage === 'error'
                        ? `エラー: ${jobError}`
                        : jobStage === 'done'
                          ? '最新の探索が完了。下に試行クエリを表示しています。'
                          : 'まだ実行していません。おすすめ生成で自動的に走ります。'}
              </p>
              <div className="agent-steps">
                <span className={`agent-chip ${stageToChip(jobStage, 'plan')}`}>クエリ生成</span>
                <span className={`agent-chip ${stageToChip(jobStage, 'crawl')}`}>フィード取得</span>
                <span className={`agent-chip ${stageToChip(jobStage, 'rank')}`}>スコアリング / リファイン</span>
                {jobQueries.map((q, idx) => (
                  <span className="agent-chip soft" key={`${q}-${idx}`}>
                    {idx + 1} 回目: {q || 'キーワード未設定'}
                  </span>
                ))}
              </div>
            </div>
          </div>
        </div>

      </div>

      <div className="agent-log">
        <p className="section-label">詳細ログ（新しい順）</p>
        {logs.length === 0 ? (
          <p className="muted">まだログはありません。「おすすめを取得」で実行ログが表示されます。</p>
        ) : (
          <ol>
            {logs.map((entry, idx) => (
              <li key={`${entry}-${idx}`}>{entry}</li>
            ))}
          </ol>
        )}
      </div>
    </section>
  )
}
