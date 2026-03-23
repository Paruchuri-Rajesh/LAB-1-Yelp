import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
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
    content:
      'Hi! I can recommend restaurants using your saved preferences, refine follow-up requests, and check current hours or trending spots when needed.',
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

function needsBrowserLocation(message) {
  return /\b(near me|around me|nearby|close to me|best rated near me)\b/i.test(message || '')
}

function sanitizeConversation(messages) {
  return (messages || [])
    .filter((message) => {
      if (!message || !message.role) return false
      if (message.role === 'assistant') {
        return Boolean((message.content || '').trim()) || Boolean(message.recommendations?.length)
      }
      return Boolean((message.content || '').trim())
    })
    .map((message) => ({
      role: message.role,
      content: message.content || '',
      recommendations: message.recommendations || [],
      parsed_filters: message.parsed_filters,
      route: message.route,
    }))
}

async function getBrowserLocation() {
  return new Promise((resolve) => {
    if (!navigator.geolocation) {
      resolve(null)
      return
    }

    navigator.geolocation.getCurrentPosition(
      (position) => {
        resolve({
          latitude: position.coords.latitude,
          longitude: position.coords.longitude,
        })
      },
      () => resolve(null),
      {
        enableHighAccuracy: true,
        timeout: 8000,
        maximumAge: 300000,
      }
    )
  })
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

  const payloadHistory = useMemo(() => sanitizeConversation(messages), [messages])

  const resetConversation = useCallback(() => {
    setMessages(INITIAL_MESSAGES)
    setInput('')
    setThinking(false)
  }, [])

  const send = useCallback(
    async (overrideMessage) => {
      const outgoing = String(overrideMessage ?? input).trim()
      if (!outgoing || thinking) return

      const userMsg = { role: 'user', content: outgoing }
      const clientLocation = needsBrowserLocation(outgoing) ? await getBrowserLocation() : null
      const payload = {
        message: outgoing,
        conversation_history: payloadHistory,
        client_location: clientLocation,
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

      const finalizeAssistant = (conversationHistory, route) => {
        if (!Array.isArray(conversationHistory) || conversationHistory.length === 0) return
        setMessages((current) => {
          const prior = current.filter((m) => m.role !== 'assistant' || (m.content || '').trim() || (m.recommendations || []).length)
          const merged = []
          for (const item of conversationHistory) {
            if (item?.role === 'assistant' || item?.role === 'user') {
              merged.push({
                role: item.role,
                content: item.content || '',
                recommendations: item.recommendations || [],
                parsed_filters: item.parsed_filters,
                route: item.route || route,
              })
            }
          }
          return merged.length ? merged : prior
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
                  finalizeAssistant(event.conversation_history, event.route)
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
          setMessages((current) => [
            ...current.filter((m) => m.role !== 'assistant' || (m.content || '').trim() || (m.recommendations || []).length),
            userMsg,
            {
              role: 'assistant',
              content: data.assistant_text || 'Sorry, I had trouble processing that.',
              recommendations: data.recommendations || [],
              route: data.route,
            },
          ])
        } catch (fallbackError) {
          setMessages((current) => [
            ...current.filter((m) => m.role !== 'assistant' || (m.content || '').trim() || (m.recommendations || []).length),
            userMsg,
            {
              role: 'assistant',
              content: 'Sorry, I had trouble processing that request.',
              recommendations: [],
            },
          ])
        } finally {
          setThinking(false)
        }
      } finally {
        setThinking(false)
      }
    },
    [input, payloadHistory, thinking]
  )

  return (
    <div className="fixed bottom-4 right-4 z-50 w-[min(92vw,440px)] max-w-full">
      <div className="overflow-hidden rounded-[28px] border border-gray-200 bg-white shadow-2xl">
        <div className="flex items-center justify-between border-b border-gray-200 px-5 py-4">
          <div className="min-w-0">
            <h3 className="text-[18px] font-semibold text-gray-900">AI Assistant</h3>
            <p className="mt-1 pr-4 text-sm leading-6 text-gray-500">
              Ask for recommendations, follow-ups, or current restaurant context.
            </p>
          </div>

          <div className="ml-3 flex shrink-0 items-center gap-2">
            <button
              type="button"
              onClick={resetConversation}
              className="text-sm font-medium text-gray-500 hover:text-gray-700"
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
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                <path d="M6 12H18" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </button>
          </div>
        </div>

        {!minimized && (
          <>
            <div className="border-b border-gray-200 px-4 py-3">
              <div className="flex flex-wrap gap-3">
                {QUICK_ACTIONS.map((suggestion) => (
                  <button
                    key={suggestion}
                    type="button"
                    onClick={() => send(suggestion)}
                    className="rounded-full border border-gray-200 bg-gray-50 px-4 py-2 text-sm font-medium text-gray-700 transition hover:bg-gray-100"
                  >
                    {suggestion}
                  </button>
                ))}
              </div>
            </div>

            <div ref={messagesRef} className="max-h-[56vh] overflow-y-auto overflow-x-hidden px-4 py-4">
              <div className="space-y-4">
                {messages.map((message, index) => (
                  <div key={`${message.role}-${index}`} className="max-w-full">
                    <div className={message.role === 'user' ? 'text-right' : 'text-left'}>
                      <div
                        className={`inline-block max-w-[88%] break-words rounded-[24px] px-4 py-3 text-[15px] leading-7 ${
                          message.role === 'user'
                            ? 'ml-auto bg-gray-100 text-gray-900'
                            : 'mr-auto bg-red-50 text-gray-900'
                        }`}
                      >
                        {message.role === 'assistant' ? (
                          <div className="prose prose-sm max-w-full overflow-hidden prose-headings:my-0 prose-li:my-0 prose-ol:my-1 prose-p:my-0 prose-ul:my-1">
                            <ReactMarkdown>{message.content || ''}</ReactMarkdown>
                          </div>
                        ) : (
                          <span>{message.content}</span>
                        )}
                      </div>
                    </div>

                    {!!message.recommendations?.length && (
                      <div className="mt-3 space-y-3">
                        {message.recommendations.map((restaurant, idx) => (
                          <div key={restaurant.id || `${index}-${idx}`} className="w-full max-w-full">
                            <RestaurantCard restaurant={restaurant} index={idx} horizontal={false} />
                            {restaurant.reason ? (
                              <p className="mt-2 break-words rounded-2xl bg-gray-50 px-3 py-2 text-sm leading-6 text-gray-600">
                                {restaurant.reason}
                              </p>
                            ) : null}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                ))}

                {thinking && (
                  <div className="text-left">
                    <div className="inline-block rounded-[24px] bg-red-50 px-4 py-3 text-sm text-gray-500">
                      Thinking...
                    </div>
                  </div>
                )}
              </div>
            </div>

            <div className="border-t border-gray-200 bg-white px-4 py-4">
              <div className="flex items-end gap-3">
                <input
                  value={input}
                  onChange={(event) => setInput(event.target.value)}
                  onKeyDown={(event) => {
                    if (event.key === 'Enter' && !event.shiftKey) {
                      event.preventDefault()
                      send()
                    }
                  }}
                  placeholder="Try 'cheap vegan dinner tonight in San Jose'"
                  className="min-w-0 flex-1 rounded-full border border-gray-200 px-4 py-3 text-base text-gray-900 outline-none placeholder:text-gray-400 focus:border-red-300"
                />
                <button
                  type="button"
                  onClick={() => send()}
                  disabled={thinking || !input.trim()}
                  className="shrink-0 rounded-full bg-red-600 px-6 py-3 text-base font-semibold text-white transition hover:bg-red-700 disabled:cursor-not-allowed disabled:opacity-60"
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
