import type { Recommendation } from '../lib/types'
import { RecoCard } from './RecoCard'

interface RecoListProps {
  items: Recommendation[]
  onOpenArticle?: (slug: string) => void
}

export function RecoList({ items, onOpenArticle }: RecoListProps) {
  if (items.length === 0) {
    return <p className="muted">まだ推薦はありません。プロフィールを保存して「おすすめを取得」を押してください。</p>
  }

  return (
    <div className="reco-list">
      {items.map((item) => (
        <RecoCard key={item.id} item={item} onOpenArticle={onOpenArticle} />
      ))}
    </div>
  )
}
