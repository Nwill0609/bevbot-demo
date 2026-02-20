import ReactMarkdown from 'react-markdown'
import type { Message } from '../App'

interface Props {
  message: Message
  isLoading?: boolean
}

const styles: Record<string, React.CSSProperties> = {
  row: {
    display: 'flex',
    gap: '12px',
    maxWidth: '800px',
    width: '100%',
  },
  userRow: {
    alignSelf: 'flex-end',
    flexDirection: 'row-reverse',
  },
  assistantRow: {
    alignSelf: 'flex-start',
  },
  avatar: {
    width: '36px',
    height: '36px',
    borderRadius: '50%',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontSize: '18px',
    flexShrink: 0,
    marginTop: '2px',
  },
  botAvatar: {
    background: 'linear-gradient(135deg, #059669, #34d399)',
    boxShadow: '0 2px 8px rgba(52, 211, 153, 0.4)',
  },
  userAvatar: {
    background: 'rgba(52, 211, 153, 0.15)',
    border: '1px solid rgba(52, 211, 153, 0.3)',
  },
  bubble: {
    padding: '12px 16px',
    borderRadius: '16px',
    maxWidth: '680px',
    fontSize: '14px',
    lineHeight: 1.6,
  },
  userBubble: {
    background: 'rgba(52, 211, 153, 0.15)',
    border: '1px solid rgba(52, 211, 153, 0.3)',
    color: '#d1fae5',
    borderTopRightRadius: '4px',
  },
  assistantBubble: {
    background: 'rgba(255,255,255,0.05)',
    border: '1px solid rgba(255,255,255,0.1)',
    color: '#ecfdf5',
    borderTopLeftRadius: '4px',
  },
  dots: {
    display: 'flex',
    gap: '4px',
    padding: '4px 0',
  },
  dot: {
    width: '6px',
    height: '6px',
    borderRadius: '50%',
    background: '#34d399',
  },
}

export default function ChatMessage({ message, isLoading }: Props) {
  const isUser = message.role === 'user'

  return (
    <div style={{ ...styles.row, ...(isUser ? styles.userRow : styles.assistantRow) }}>
      <div style={{ ...styles.avatar, ...(isUser ? styles.userAvatar : styles.botAvatar) }}>
        {isUser ? '👤' : '🍹'}
      </div>
      <div style={{ ...styles.bubble, ...(isUser ? styles.userBubble : styles.assistantBubble) }}>
        {isLoading ? (
          <div style={styles.dots}>
            {[0, 1, 2].map(i => (
              <div
                key={i}
                style={{
                  ...styles.dot,
                  animation: `bounce 1.2s ${i * 0.2}s infinite ease-in-out`,
                }}
              />
            ))}
            <style>{`
              @keyframes bounce {
                0%, 80%, 100% { transform: translateY(0); opacity: 0.4; }
                40% { transform: translateY(-6px); opacity: 1; }
              }
            `}</style>
          </div>
        ) : isUser ? (
          <span style={{ whiteSpace: 'pre-wrap' }}>{message.content}</span>
        ) : (
          <div className="markdown-body">
            <ReactMarkdown>{message.content}</ReactMarkdown>
          </div>
        )}
      </div>
    </div>
  )
}
