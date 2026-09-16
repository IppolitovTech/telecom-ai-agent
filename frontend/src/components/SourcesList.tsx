import type { Source } from '../api/types'
import { formatDocumentTitle } from '../lib/sources'

interface SourcesListProps {
  sources: Source[]
}

export function SourcesList({ sources }: SourcesListProps) {
  if (sources.length === 0) return null

  return (
    <div className="sources">
      <p className="sources__title">Ответ основан на:</p>
      <ul>
        {sources.map((source, index) => (
          <li key={`${source.document}-${source.chunk}-${index}`}>
            {formatDocumentTitle(source.document)} — раздел {source.chunk + 1}
          </li>
        ))}
      </ul>
    </div>
  )
}
