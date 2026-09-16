import type { ChatMessage } from '../api/types'
import { AgentActivity } from './AgentActivity'
import { SourcesList } from './SourcesList'

interface ChatMessageItemProps {
  message: ChatMessage
}

export function ChatMessageItem({ message }: ChatMessageItemProps) {
  if (message.role === 'user') {
    return (
      <li className="message message--user">
        <p>{message.content}</p>
      </li>
    )
  }

  return (
    <li className="message message--assistant">
      <AgentActivity sources={message.sources} toolCalls={message.toolCalls} error={message.error} />
      <p>{message.content}</p>
      <SourcesList sources={message.sources} />
    </li>
  )
}
