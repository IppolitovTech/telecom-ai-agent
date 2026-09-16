// Mirrors backend/models/chat.py — keep in sync if the Pydantic schema changes.

export interface ChatRequest {
  message: string
  session_id: string
}

export interface ToolCall {
  name: string
  args: Record<string, unknown>
}

export interface Source {
  document: string
  chunk: number
  score: number
}

export interface ChatResponse {
  reply: string
  tool_calls: ToolCall[]
  sources: Source[]
  error: boolean
}

export type ChatMessage =
  | {
      id: string
      role: 'user'
      content: string
    }
  | {
      id: string
      role: 'assistant'
      content: string
      toolCalls: ToolCall[]
      sources: Source[]
      error: boolean
    }
