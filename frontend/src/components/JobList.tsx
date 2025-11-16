import type { JobSummary } from '../lib/types'

interface JobListProps {
  items: JobSummary[]
  mainSkill?: string
  targetRole?: string
}

export function JobList({ items, mainSkill, targetRole }: JobListProps) {
  if (items.length === 0) {
    return <p className="muted">求人がまだ取得されていません。キーワードを入れて再実行してください。</p>
  }

  const normalizeLocation = (loc?: string | null) => {
    if (!loc) return '勤務地/リモート条件';
    const lower = loc.toLowerCase();
    if (lower === 'jp' || lower === 'japan') return '日本（勤務地/リモート条件明示）';
    if (lower.includes('remote')) return 'フルリモート可';
    if (lower.includes('tokyo')) return '東京圏';
    return loc;
  };

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
            {job.location && <span>{normalizeLocation(job.location)}</span>}
            {job.published_at && <span>{new Date(job.published_at).toLocaleDateString()}</span>}
          </div>
          <div className="job-summary">
            {job.snippet ? <p className="job-snippet">{job.snippet}</p> : <p className="job-snippet muted">概要は求人票からご確認ください。</p>}
            <div className="job-reason">
              <p className="section-label">おすすめ理由</p>
              <ul>
                <li>
                  スキル適合: {mainSkill ?? '登録スキル'} を活かしつつ、{job.title} が求める技術スタックと重なる部分が多いです。
                </li>
                <li>
                  成長余地: {targetRole ?? '目標ロール'} に近い裁量・責任範囲があり、次のタイトルへ進む実績を作りやすいです。
                </li>
                <li>働き方: {normalizeLocation(job.location)} が明示されており、通勤/リモート条件のギャップを事前に把握できます。</li>
              </ul>
            </div>
          </div>
          <div className="job-actions">
            <a href={job.url} target="_blank" rel="noreferrer" className="ghost">
              JD を開く
            </a>
          </div>
        </article>
      ))}
    </div>
  )
}
