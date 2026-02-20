import { useState, useRef } from 'react'

interface Props {
  onSend: (text: string) => void
  disabled?: boolean
}

export default function ChatInput({ onSend, disabled }: Props) {
  const [value, setValue] = useState('')
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  const handleSend = () => {
    const text = value.trim()
    if (!text || disabled) return
    onSend(text)
    setValue('')
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const handleInput = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setValue(e.target.value)
    const ta = e.target
    ta.style.height = 'auto'
    ta.style.height = Math.min(ta.scrollHeight, 160) + 'px'
  }

  return (
    <div
      style={{
        display: 'flex',
        gap: '10px',
        alignItems: 'flex-end',
        background: 'rgba(255,255,255,0.05)',
        border: '1px solid rgba(52, 211, 153, 0.25)',
        borderRadius: '16px',
        padding: '10px 14px',
        transition: 'border-color 0.2s',
      }}
    >
      <textarea
        ref={textareaRef}
        value={value}
        onChange={handleInput}
        onKeyDown={handleKeyDown}
        placeholder="Ask BevBot anything about flavors, inventory, orders..."
        disabled={disabled}
        rows={1}
        style={{
          flex: 1,
          background: 'transparent',
          border: 'none',
          outline: 'none',
          color: '#d1fae5',
          fontSize: '14px',
          lineHeight: 1.6,
          resize: 'none',
          fontFamily: 'inherit',
          maxHeight: '160px',
          overflow: 'auto',
          opacity: disabled ? 0.5 : 1,
        }}
      />
      <button
        onClick={handleSend}
        disabled={!value.trim() || disabled}
        style={{
          width: '36px',
          height: '36px',
          borderRadius: '10px',
          border: 'none',
          background: value.trim() && !disabled
            ? 'linear-gradient(135deg, #059669, #34d399)'
            : 'rgba(52, 211, 153, 0.15)',
          cursor: value.trim() && !disabled ? 'pointer' : 'not-allowed',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: '16px',
          transition: 'all 0.2s ease',
          flexShrink: 0,
          boxShadow: value.trim() && !disabled ? '0 2px 8px rgba(52,211,153,0.4)' : 'none',
        }}
        title="Send (Enter)"
      >
        ➤
      </button>
    </div>
  )
}
