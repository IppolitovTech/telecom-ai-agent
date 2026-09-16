import { useCallback, useState } from 'react'
import { sendChatMessage } from '../api/client'
import type { ChatMessage } from '../api/types'
import { useSessionId } from './useSessionId'

// Generous enough to cover the `combined` branch's ReAct loop, which can chain
// several sequential LLM calls (each capped server-side by settings.llm_timeout_s).
const REQUEST_TIMEOUT_MS = 60_000

export type ChatStatus = 'idle' | 'loading' | 'error'

export function useChat() {
  const sessionId = useSessionId()
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [status, setStatus] = useState<ChatStatus>('idle')

  const sendMessage = useCallback(
    async (text: string) => {
      const trimmed = text.trim()
      if (!trimmed || status === 'loading') return

      setMessages((prev) => [...prev, { id: crypto.randomUUID(), role: 'user', content: trimmed }])
      setStatus('loading')

      const controller = new AbortController()
      let timedOut = false
      const timeout = setTimeout(() => {
        timedOut = true
        controller.abort()
      }, REQUEST_TIMEOUT_MS)

      try {
        const response = await sendChatMessage({ message: trimmed, session_id: sessionId }, controller.signal)
        setMessages((prev) => [
          ...prev,
          {
            id: crypto.randomUUID(),
            role: 'assistant',
            content: response.reply,
            toolCalls: response.tool_calls,
            sources: response.sources,
            error: response.error,
          },
        ])
        setStatus('idle')
      } catch {
        const content = timedOut
          ? 'Модель слишком долго не отвечает. Попробуйте, пожалуйста, ещё раз.'
          : 'Не удалось подключиться к серверу. Проверьте соединение и попробуйте ещё раз.'
        setMessages((prev) => [
          ...prev,
          {
            id: crypto.randomUUID(),
            role: 'assistant',
            content,
            toolCalls: [],
            sources: [],
            error: true,
          },
        ])
        setStatus('error')
      } finally {
        clearTimeout(timeout)
      }
    },
    [sessionId, status],
  )

  return { messages, status, sendMessage }
}
