import { useEffect, useRef } from 'react'
import { useChat } from '../hooks/useChat'
import { ChatInput } from './ChatInput'
import { ChatMessageItem } from './ChatMessageItem'

export function ChatWindow() {
  const { messages, status, sendMessage } = useChat()
  const endRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const isSubmitting = status === 'loading'

  return (
    <div className="chat">
      <header className="chat__header">
        <h1>Техподдержка Telecom</h1>
      </header>

      <ul className="chat__messages">
        {messages.length === 0 && (
          <li className="chat__empty">Задайте вопрос о тарифах, настройке роутера или создайте заявку.</li>
        )}

        {messages.map((message) => (
          <ChatMessageItem key={message.id} message={message} />
        ))}

        {isSubmitting && (
          <li className="message message--assistant message--loading" aria-live="polite">
            <span className="typing-indicator" aria-hidden="true">
              <span />
              <span />
              <span />
            </span>
            Печатает…
          </li>
        )}

        <div ref={endRef} />
      </ul>

      <ChatInput disabled={isSubmitting} onSend={sendMessage} />
    </div>
  )
}
