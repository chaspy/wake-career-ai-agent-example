import type { Recommendation } from '../lib/types'

interface RecoCardProps {
  item: Recommendation
  onOpenArticle?: (slug: string) => void
}

export function RecoCard({ item, onOpenArticle }: RecoCardProps) {
  return (
    <article className="reco-card">
      <header>
        <div>
          <p className="eyebrow small">おすすめコンテンツ</p>
          <a href={item.url} target="_blank" rel="noreferrer" className="reco-link">
            <h3>{item.title}</h3>
          </a>
        </div>
        <span className="score-pill">score {item.score.toFixed(2)}</span>
      </header>
      <div className="reco-body">
        <p className="excerpt">{item.excerpt}</p>
        {item.reasons.length > 0 && (
          <div className="reason-block">
            <span className="section-label">おすすめ理由</span>
            <ul className="reasons">
              {item.reasons.map((reason) => (
                <li key={reason}>{reason}</li>
              ))}
            </ul>
          </div>
        )}
        {item.citations.length > 0 && (
          <div className="citations">
            <span className="section-label">引用元</span>
            <ul>
              {item.citations.map((citation) => (
                <li key={`${citation.source_url}-${citation.line ?? '0'}`}>
                  <a href={citation.source_url} target="_blank" rel="noreferrer">
                    {citation.title} {citation.line ? `L${citation.line}` : ''}
                  </a>
                </li>
              ))}
            </ul>
          </div>
        )}
        {onOpenArticle && (
          <button className="ghost" onClick={() => onOpenArticle(item.id)}>
            本文をプレビュー
          </button>
        )}
      </div>
    </article>
  )
}
