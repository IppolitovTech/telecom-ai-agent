import type { Source, ToolCall } from '../api/types'

interface AgentActivityProps {
  sources: Source[]
  toolCalls: ToolCall[]
  error: boolean
}

export function AgentActivity({ sources, toolCalls, error }: AgentActivityProps) {
  const steps: string[] = []

  if (sources.length > 0) {
    steps.push(`Retrieved ${sources.length} relevant document${sources.length === 1 ? '' : 's'}`)
  }
  for (const call of toolCalls) {
    steps.push(`Called ${call.name}`)
  }
  steps.push(error ? 'Encountered an error' : 'Generated response')

  return (
    <div className="agent-activity">
      <p className="agent-activity__title">Agent activity</p>
      <ul>
        {steps.map((step, index) => {
          const isLast = index === steps.length - 1
          return (
            <li key={index} className={error && isLast ? 'is-error' : undefined}>
              <span aria-hidden="true">{error && isLast ? '⚠' : '✓'}</span> {step}
            </li>
          )
        })}
      </ul>
    </div>
  )
}
