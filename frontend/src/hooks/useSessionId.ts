import { useState } from 'react'

const STORAGE_KEY = 'session_id'

function readOrCreateSessionId(): string {
  const existing = localStorage.getItem(STORAGE_KEY)
  if (existing) return existing

  const created = crypto.randomUUID()
  localStorage.setItem(STORAGE_KEY, created)
  return created
}

export function useSessionId(): string {
  const [sessionId] = useState(readOrCreateSessionId)
  return sessionId
}
