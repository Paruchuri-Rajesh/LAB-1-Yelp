import { useCallback, useEffect, useRef, useState } from 'react'
import ReactMarkdown from 'react-markdown'
import RestaurantCard from '../restaurants/RestaurantCard'

const QUICK_ACTIONS = [
  'Find dinner tonight',
  'Best rated near me',
  'Vegan options',
  'Something romantic for an anniversary',
]

const INITIAL_MESSAGES = [
  {
    role: 'assistant',
    content: 'Hi! I can recommend restaurants using your saved preferences, refine follow-up requests, and check current hours or trending spots when needed.',
    recommendations: [],
  },
]

function getAuthHeaders() {
  const headers = {
    'Content-Type': 'application/json',
    Accept: 'text/event-stream',
  }
  const token = localStorage.getItem('access_token')
  if (token) headers.Authorization = `Bearer ${token}`
  return headers
}

export default function ChatWidget() {
  const [messages, setMessages] = useState(INITIAL_MESSAGES)
  const [input, setInput] = useState('')
  const [thinking, setThinking] = useState(false)
  const [minimized, setMinimized] = useState(false)
  const messagesRef = useRef(null)

  useEffect(() => {
    if (messagesRef.current) {
      messagesRef.current.scrollTop = messagesRef.current.scrollHeight
    }
  }, [messages, thinking])

  const resetConversation = useCallback(() => {
    setMessages(INITIAL_MESSAGES)
    setInput('')
    setThinking(false)
  }, [])

  const send = useCallback(async (overrideMessage) => {
    const outgoing = (overrideMessage ?? input).trim()
    if (!outgoing || thinking) return

    const userMsg = { role: 'user', content: outgoing }
    const payload = {
      message: outgoing,
      conversation_history: messages.map((message) => ({
        role: message.role,
        content: message.content,
        recommendations: message.recommendations || [],
      })),
    }

    setThinking(true)
    setInput('')
    setMessages((current) => [...current, userMsg, { role: 'assistant', content: '', recommendations: [] }])

    const appendToAssistant = (text) => {
      setMessages((current) => {
        const copy = [...current]
        for (let i = copy.length - 1; i >= 0; i -= 1) {
          if (copy[i].role === 'assistant') {
            copy[i] = { ...copy[i], content: `${copy[i].content || ''}${text}` }
            break
          }
        }
        return copy
      })
    }

    const appendRecommendation = (item) => {
      setMessages((current) => {
        const copy = [...current]
        for (let i = copy.length - 1; i >= 0; i -= 1) {
          if (copy[i].role === 'assistant') {
            copy[i] = {
              ...copy[i],
              recommendations: [...(copy[i].recommendations || []), item],
            }
            break
          }
        }
        return copy
      })
    }

    try {
      const response = await fetch('/api/v1/ai-assistant/chat/stream', {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify(payload),
      })

      if (!response.ok || !response.body) {
        throw new Error('stream unavailable')
      }

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })
        const events = buffer.split('\n\n')
        buffer = events.pop() || ''

        for (const eventBlock of events) {
          const line = eventBlock.trim()
          if (!line) continue
          const dataLines = line
            .split('\n')
            .filter(Boolean)
            .map((part) => part.replace(/^data:\s?/, ''))

          for (const dataLine of dataLines) {
            try {
              const event = JSON.parse(dataLine)
              if (event.type === 'assistant_chunk' && event.text) {
                appendToAssistant(event.text)
              }
              if (event.type === 'recommendation' && event.item) {
                appendRecommendation(event.item)
              }
              if (event.type === 'done') {
                setThinking(false)
              }
            } catch (error) {
              console.error('Failed to parse chat stream event', error)
            }
          }
        }
      }
    } catch (error) {
      try {
        const fallback = await fetch('/api/v1/ai-assistant/chat', {
          method: 'POST',
          headers: getAuthHeaders(),
          body: JSON.stringify(payload),
        })
        const data = await fallback.json()
        setMessages((current) => {
          const copy = [...current]
          for (let i = copy.length - 1; i >= 0; i -= 1) {
            if (copy[i].role === 'assistant') {
              copy[i] = {
                ...copy[i],
                content: data.assistant_text || 'Sorry, I had trouble processing that.',
                recommendations: data.recommendations || [],
              }
              break
            }
          }
          return copy
        })
      } catch (fallbackError) {
        setMessages((current) => {
          const copy = [...current]
          for (let i = copy.length - 1; i >= 0; i -= 1) {
            if (copy[i].role === 'assistant') {
              copy[i] = {
                ...copy[i],
                content: 'Sorry, I had trouble processing that request.',
                recommendations: [],
              }
              break
            }
          }
          return copy
        })
      } finally {
        setThinking(false)
      }
    }
  }, [input, messages, thinking])

  return (
    <div
      className="fixed bottom-6 right-6 z-50 w-[380px]"
      style={{ minWidth: 300, minHeight: 150, maxWidth: 760, maxHeight: 900, resize: 'both', overflow: 'auto' }}
    >
      <div className="rounded-2xl border border-gray-200 bg-white shadow-xl">
        <div className="border-b px-4 py-3">
          <div className="flex items-center justify-between gap-3">
            <div>
              <h3 className="text-sm font-semibold text-gray-900">AI Assistant</h3>
              <p className="mt-1 text-xs text-gray-500">Ask for recommendations, follow-ups, or current restaurant context.</p>
            </div>
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={resetConversation}
                className="text-xs text-gray-500 hover:text-gray-700"
                aria-label="New conversation"
                title="New conversation"
              >
                New
              </button>
              <button
                type="button"
                onClick={() => setMinimized((value) => !value)}
                className="rounded-full p-1 text-gray-500 hover:bg-gray-100 hover:text-gray-700"
                aria-label={minimized ? 'Open chat' : 'Minimize chat'}
                title={minimized ? 'Open chat' : 'Minimize chat'}
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden>
                  <path d="M6 12H18" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
              </button>
            </div>
          </div>
        </div>

        {!minimized && (
          <>
            <div className="border-b px-4 py-3">
              <div className="flex flex-wrap gap-2">
                {QUICK_ACTIONS.map((action) => (
                  <button
                    key={action}
                    type="button"
                    onClick={() => send(action)}
                    className="rounded-full border border-gray-200 bg-gray-50 px-3 py-1 text-xs text-gray-700 hover:bg-gray-100"
                  >
                    {action}
                  </button>
                ))}
              </div>
            </div>

            <div ref={messagesRef} className="max-h-[60vh] space-y-3 overflow-auto px-4 py-3">
              {messages.map((message, index) => (
                <div key={`${message.role}-${index}`} className={message.role === 'user' ? 'text-right' : 'text-left'}>
                  <div className={`inline-block max-w-[88%] rounded-2xl px-3 py-2 text-sm ${message.role === 'user' ? 'bg-gray-100 text-gray-900' : 'bg-red-50 text-gray-900'}`}>
                    {message.role === 'assistant' ? <ReactMarkdown>{message.content || ''}</ReactMarkdown> : <span>{message.content}</span>}
                  </div>
                  {message.recommendations?.length > 0 && (
                    <div className="mt-3 space-y-3">
                      {message.recommendations.map((restaurant) => (
                        <div key={restaurant.id} className="space-y-1">
                          <RestaurantCard restaurant={restaurant} horizontal />
                          {restaurant.reason && <p className="text-left text-xs text-gray-600">{restaurant.reason}</p>}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ))}
              {thinking && <div className="text-left text-sm text-gray-500">Thinking…</div>}
            </div>

            <div className="px-3 py-3">
              <div className="flex gap-2">
                <input
                  value={input}
                  onChange={(event) => setInput(event.target.value)}
                  onKeyDown={(event) => {
                    if (event.key === 'Enter') send()
                  }}
                  placeholder="Try 'cheap vegan dinner tonight in San Jose'"
                  className="flex-1 rounded-2xl border border-gray-200 px-3 py-2 text-sm outline-none"
                />
                <button
                  type="button"
                  onClick={() => send()}
                  disabled={thinking}
                  className="rounded-2xl bg-red-600 px-4 py-2 text-sm font-semibold text-white disabled:opacity-60"
                >
                  Send
                </button>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  )
}
