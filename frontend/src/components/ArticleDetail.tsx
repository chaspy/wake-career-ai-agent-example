import type { ArticleDetail } from '../lib/types'

interface ArticleDetailProps {
  article: ArticleDetail
  onClose: () => void
}

export function ArticleDetail({ article, onClose }: ArticleDetailProps) {
  return (
    <div className="modal-backdrop" role="dialog" aria-modal="true">
      <div className="modal-panel">
        <header>
          <div>
            <p className="badge">{article.category ?? 'WAKE Article'}</p>
            <h3>{article.title}</h3>
            <a href={article.source_url} target="_blank" rel="noreferrer">
              元記事を開く
            </a>
          </div>
          <button className="ghost" onClick={onClose}>
            閉じる
          </button>
        </header>
        <div className="article-meta">
          <span>公開日: {article.published ?? 'N/A'}</span>
          {article.tags.length > 0 && <span>タグ: {article.tags.join(', ')}</span>}
        </div>
        <article className="article-body">{article.body}</article>
      </div>
    </div>
  )
}
