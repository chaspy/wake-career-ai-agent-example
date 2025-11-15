import type { JobSummary } from '../lib/types'

interface JobListProps {
  items: JobSummary[]
}

export function JobList({ items }: JobListProps) {
  if (items.length === 0) {
    return <p className="muted">求人がまだ取得されていません。キーワードを入れて再実行してください。</p>
  }

  return (
    <div className="job-list">
      {items.map((job) => (
        <article className="job-card" key={job.id}>
          <header>
            <div>
              <p className="eyebrow small">{job.source}</p>
              <a href={job.url} target="_blank" rel="noreferrer" className="job-link">
                <h3>{job.title}</h3>
              </a>
            </div>
            {job.company && <span className="job-company">{job.company}</span>}
          </header>
          <div className="job-meta">
            {job.location && <span>{job.location}</span>}
            {job.published_at && <span>{new Date(job.published_at).toLocaleDateString()}</span>}
          </div>
          {job.snippet && <p className="job-snippet">{job.snippet}</p>}
          <a href={job.url} target="_blank" rel="noreferrer" className="ghost">
            詳細を見る
          </a>
        </article>
      ))}
    </div>
  )
}
