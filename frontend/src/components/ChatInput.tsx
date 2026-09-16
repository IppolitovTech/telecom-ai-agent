import { useState, type FormEvent } from 'react'

interface ChatInputProps {
  disabled: boolean
  onSend: (text: string) => void
}

export function ChatInput({ disabled, onSend }: ChatInputProps) {
  const [value, setValue] = useState('')

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault()
    if (disabled || !value.trim()) return
    onSend(value)
    setValue('')
  }

  return (
    <form className="chat-input" onSubmit={handleSubmit}>
      <input
        type="text"
        value={value}
        onChange={(event) => setValue(event.target.value)}
        placeholder="Введите сообщение..."
        disabled={disabled}
        aria-label="Сообщение"
      />
      <button type="submit" disabled={disabled || !value.trim()}>
        Отправить
      </button>
    </form>
  )
}
