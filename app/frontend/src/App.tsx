import { useState, useRef, useEffect } from 'react'
import ChatMessage from './components/ChatMessage'
import ChatInput from './components/ChatInput'

export interface Message {
  role: 'user' | 'assistant'
  content: string
}

const STARTER_PROMPTS = [
  { icon: '📈', text: 'What flavor is trending right now?' },
  { icon: '🔍', text: "We're out of Guava — what's a similar flavor profile?" },
  { icon: '💰', text: 'What does our supplier charge for Hibiscus? Use SKU HB-001 and quantity 50000 ml' },
  { icon: '🛒', text: 'Order 50 liters of Hibiscus. SKU is HB-001, ingredient ID is ING004, quantity is 50000 ml' },
]

const styles: Record<string, React.CSSProperties> = {
  app: {
    display: 'flex',
    flexDirection: 'column',
    height: '100vh',
    background: 'linear-gradient(135deg, #0d1f1a 0%, #0f2d24 50%, #112b20 100%)',
    color: '#f0fdf4',
  },
  header: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
    padding: '16px 24px',
    borderBottom: '1px solid rgba(52, 211, 153, 0.2)',
    background: 'rgba(0,0,0,0.3)',
    backdropFilter: 'blur(8px)',
  },
  logo: {
    fontSize: '28px',
  },
  headerText: {
    display: 'flex',
    flexDirection: 'column',
  },
  title: {
    fontSize: '20px',
    fontWeight: 700,
    color: '#34d399',
    letterSpacing: '-0.3px',
  },
  subtitle: {
    fontSize: '12px',
    color: '#6ee7b7',
    opacity: 0.8,
  },
  backButton: {
    display: 'flex',
    alignItems: 'center',
    gap: '6px',
    padding: '6px 12px',
    background: 'rgba(52, 211, 153, 0.1)',
    border: '1px solid rgba(52, 211, 153, 0.3)',
    borderRadius: '8px',
    color: '#6ee7b7',
    fontSize: '13px',
    cursor: 'pointer',
    transition: 'all 0.2s ease',
  },
  poweredBy: {
    marginLeft: 'auto',
    fontSize: '11px',
    color: '#6ee7b7',
    opacity: 0.6,
    display: 'flex',
    alignItems: 'center',
    gap: '6px',
  },
  dot: {
    width: '6px',
    height: '6px',
    borderRadius: '50%',
    background: '#34d399',
    boxShadow: '0 0 6px #34d399',
    animation: 'pulse 2s infinite',
  },
  messages: {
    flex: 1,
    overflowY: 'auto',
    padding: '24px',
    display: 'flex',
    flexDirection: 'column',
    gap: '16px',
  },
  welcome: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    flex: 1,
    gap: '32px',
    padding: '40px 24px',
  },
  welcomeTitle: {
    fontSize: '32px',
    fontWeight: 700,
    color: '#34d399',
    textAlign: 'center',
  },
  welcomeSubtitle: {
    fontSize: '16px',
    color: '#a7f3d0',
    textAlign: 'center',
    maxWidth: '480px',
    lineHeight: 1.6,
    opacity: 0.9,
  },
  promptsLabel: {
    fontSize: '13px',
    color: '#6ee7b7',
    textTransform: 'uppercase',
    letterSpacing: '1px',
    opacity: 0.7,
  },
  promptsGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(2, 1fr)',
    gap: '12px',
    width: '100%',
    maxWidth: '640px',
  },
  promptCard: {
    display: 'flex',
    alignItems: 'flex-start',
    gap: '10px',
    padding: '14px 16px',
    background: 'rgba(52, 211, 153, 0.08)',
    border: '1px solid rgba(52, 211, 153, 0.2)',
    borderRadius: '12px',
    cursor: 'pointer',
    transition: 'all 0.2s ease',
    textAlign: 'left',
    color: '#d1fae5',
    fontSize: '13px',
    lineHeight: 1.4,
  },
  promptIcon: {
    fontSize: '18px',
    flexShrink: 0,
    marginTop: '1px',
  },
  inputArea: {
    padding: '16px 24px',
    borderTop: '1px solid rgba(52, 211, 153, 0.15)',
    background: 'rgba(0,0,0,0.3)',
  },
}

export default function App() {
  const [messages, setMessages] = useState<Message[]>([])
  const [loading, setLoading] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  const sendMessage = async (text: string) => {
    if (!text.trim() || loading) return

    const userMsg: Message = { role: 'user', content: text }
    const updatedHistory = [...messages, userMsg]
    setMessages(updatedHistory)
    setLoading(true)

    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: text,
          history: messages.map(m => ({ role: m.role, content: m.content })),
        }),
      })

      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: 'Request failed' }))
        throw new Error(err.detail || 'Request failed')
      }

      const data = await res.json()
      setMessages([...updatedHistory, { role: 'assistant', content: data.message }])
    } catch (e) {
      const errMsg = e instanceof Error ? e.message : 'Something went wrong'
      setMessages([...updatedHistory, { role: 'assistant', content: `⚠️ Error: ${errMsg}` }])
    } finally {
      setLoading(false)
    }
  }

  const isEmpty = messages.length === 0

  return (
    <div style={styles.app}>
      <style>{`
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.4; } }
        .prompt-card:hover { background: rgba(52, 211, 153, 0.15) !important; border-color: rgba(52, 211, 153, 0.5) !important; transform: translateY(-1px); }
        .back-button:hover { background: rgba(52, 211, 153, 0.2) !important; border-color: rgba(52, 211, 153, 0.6) !important; color: #a7f3d0 !important; }
        ::-webkit-scrollbar { width: 6px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: rgba(52, 211, 153, 0.3); border-radius: 3px; }
      `}</style>

      <header style={styles.header}>
        <span style={styles.logo}>🍹</span>
        <div style={styles.headerText}>
          <span style={styles.title}>BevBot</span>
          <span style={styles.subtitle}>AI Beverage Operations Assistant</span>
        </div>
        {!isEmpty && (
          <button
            className="back-button"
            style={styles.backButton}
            onClick={() => setMessages([])}
          >
            ← New Chat
          </button>
        )}
        <div style={styles.poweredBy}>
          <div style={styles.dot} />
          Databricks Agent Bricks
        </div>
      </header>

      <div style={styles.messages}>
        {isEmpty ? (
          <div style={styles.welcome}>
            <div>
              <div style={styles.welcomeTitle}>Hello! I'm BevBot 🍹</div>
              <p style={{ ...styles.welcomeSubtitle, marginTop: '12px' }}>
                I can help you track flavors, check inventory, look up supplier pricing,
                place orders, and generate drink recipes — all powered by your live data.
              </p>
            </div>
            <div style={styles.promptsLabel}>Try asking me</div>
            <div style={styles.promptsGrid}>
              {STARTER_PROMPTS.map((p, i) => (
                <button
                  key={i}
                  className="prompt-card"
                  style={styles.promptCard}
                  onClick={() => sendMessage(p.text)}
                >
                  <span style={styles.promptIcon}>{p.icon}</span>
                  <span>{p.text}</span>
                </button>
              ))}
            </div>
          </div>
        ) : (
          <>
            {messages.map((msg, i) => (
              <ChatMessage key={i} message={msg} />
            ))}
            {loading && (
              <ChatMessage
                message={{ role: 'assistant', content: '' }}
                isLoading
              />
            )}
            <div ref={messagesEndRef} />
          </>
        )}
      </div>

      <div style={styles.inputArea}>
        <ChatInput onSend={sendMessage} disabled={loading} />
      </div>
    </div>
  )
}
