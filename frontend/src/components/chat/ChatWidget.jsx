import { useCallback, useEffect, useRef, useState } from 'react'
import ReactMarkdown from 'react-markdown'
import { chat } from '../../api/ai'
import RestaurantCard from '../restaurants/RestaurantCard'

export default function ChatWidget() {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [thinking, setThinking] = useState(false)
  const [minimized, setMinimized] = useState(false)
  const messagesRef = useRef()

  useEffect(() => {
    if (messagesRef.current) messagesRef.current.scrollTop = messagesRef.current.scrollHeight
  }, [messages])

  const send = useCallback(async () => {
    if (!input.trim()) return
    const userMsg = { role: 'user', content: input }
  // add the user message together with assistant placeholder later to avoid duplicate entries
    setThinking(true)
    setInput('')

    const payload = { message: input, conversation_history: messages }

    // Try streaming endpoint first
    try {
      const res = await fetch('/api/v1/ai-assistant/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })

      if (!res.ok || !res.body) {
        throw new Error('Streaming not available')
      }

      const reader = res.body.getReader()
      const decoder = new TextDecoder()
      let buf = ''

  // Create assistant placeholder together with the user message
  setMessages((m) => [...m, userMsg, { role: 'assistant', content: '', recommendations: [] }])

      const appendToAssistant = (text) => {
        setMessages((prev) => {
          const copy = [...prev]
          // find last assistant message
          for (let i = copy.length - 1; i >= 0; i--) {
            if (copy[i].role === 'assistant') {
              copy[i] = { ...copy[i], content: (copy[i].content || '') + text }
              break
            }
          }
          return copy
        })
      }

      const pushRecommendation = (item) => {
        setMessages((prev) => {
          const copy = [...prev]
          for (let i = copy.length - 1; i >= 0; i--) {
            if (copy[i].role === 'assistant') {
              copy[i].recommendations = [...(copy[i].recommendations || []), item]
              break
            }
          }
          return copy
        })
      }

      // stream loop
      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        buf += decoder.decode(value, { stream: true })

        // process SSE-style data: split on double-newline
        const parts = buf.split('\n\n')
        buf = parts.pop() // remainder
        for (const part of parts) {
          const line = part.trim()
          if (!line) continue
          // lines may be like 'data: {...}' or multiple data: lines
          const dataLines = line.split('\n').filter(Boolean).map((l) => l.replace(/^data:\s?/, ''))
          for (const dl of dataLines) {
            try {
              const obj = JSON.parse(dl)
              if (obj.type === 'start') {
                // optionally show if Ollama/Tavily will be used
                // e.g., show a small badge or console log
                console.log('AI start meta', obj)
              } else if (obj.type === 'assistant_chunk') {
                appendToAssistant(obj.text)
              } else if (obj.type === 'recommendation') {
                pushRecommendation(obj.item)
              } else if (obj.type === 'done') {
                // finalize
                setThinking(false)
              }
            } catch (e) {
              console.error('Failed to parse SSE chunk', e, dl)
            }
          }
        }
      }

    } catch (err) {
      // fallback: call JSON endpoint
      try {
        const response = await fetch('/api/v1/ai-assistant/chat/json', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        })
        const data = await response.json()
        setMessages((m) => [...m, userMsg, { role: 'assistant', content: data.assistant_text, recommendations: data.recommendations }])
      } catch (e) {
        setMessages((m) => [...m, { role: 'assistant', content: 'Sorry, I had trouble processing that.' }])
      } finally {
        setThinking(false)
      }
    }
  }, [input, messages])

  return (
    <div
      className="fixed right-6 bottom-6 z-50 w-[360px]"
      style={{ minWidth: 280, minHeight: 120, maxWidth: 720, maxHeight: 8000, resize: 'both', overflow: 'auto' }}
    >
      <div className="rounded-2xl border border-gray-200 bg-white shadow-lg">
        <div className="px-4 py-3 border-b">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold">AI Assistant</h3>
            <div className="flex items-center gap-2">
              {/* New - clear conversation (keeps as text for discoverability) */}
              <button
                type="button"
                onClick={() => { setMessages([]); setInput('') }}
                className="text-xs text-gray-500 hover:text-gray-700"
                aria-label="New conversation"
                title="New conversation"
              >
                New
              </button>

              {/* Minimize icon */}
              <button
                type="button"
                onClick={() => setMinimized((v) => !v)}
                className="rounded-full p-1 text-gray-500 hover:bg-gray-100 hover:text-gray-700"
                aria-label={minimized ? 'Open chat' : 'Minimize chat'}
                title={minimized ? 'Open chat' : 'Minimize chat'}
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden>
                  <path d="M6 12H18" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
              </button>

              {/* Close icon */}
              <button
                type="button"
                onClick={() => { setMinimized(true); setMessages([]); setInput('') }}
                className="rounded-full p-1 text-gray-500 hover:bg-gray-100 hover:text-gray-700"
                aria-label="Close chat"
                title="Close chat"
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden>
                  <path d="M18 6L6 18" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                  <path d="M6 6l12 12" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
              </button>
            </div>
          </div>
          <p className="text-xs text-gray-500 mt-1">Ask for restaurant recommendations</p>
        </div>

        {!minimized && (
          <>
            <div ref={messagesRef} className="overflow-auto px-4 py-3 space-y-3" style={{ maxHeight: '60vh' }}>
              {messages.map((m, i) => (
                <div key={i} className={m.role === 'user' ? 'text-right' : 'text-left'}>
                  <div className={`inline-block max-w-[85%] rounded-2xl px-3 py-2 text-sm ${m.role === 'user' ? 'bg-gray-100 text-gray-900' : 'bg-red-50 text-gray-900'}`}>
                    {m.role === 'assistant' ? (
                      // Render markdown content from the LLM safely
                      <ReactMarkdown>{m.content || ''}</ReactMarkdown>
                    ) : (
                      // user messages remain plain text
                      <span>{m.content}</span>
                    )}
                  </div>
                  {m.recommendations && (
                    <div className="mt-2 space-y-2 w-full flex flex-col items-end">
                      {m.recommendations.map((r) => (
                        <div key={r.id} className="rounded-2xl flex items-start gap-3 w-full justify-end">
                          {/* Constrain card width so it displays properly inside the chat */}
                          <div className="w-[300px]">
                            <RestaurantCard restaurant={r} horizontal={true} />
                          </div>
                          <div className="flex-1 mt-2 text-xs text-gray-600">{r.reason}</div>
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
                <input value={input} onChange={(e) => setInput(e.target.value)} onKeyDown={(e) => { if (e.key === 'Enter') send() }} placeholder="Ask for something like 'vegan dinner tonight'" className="flex-1 rounded-2xl border border-gray-200 px-3 py-2 text-sm outline-none" />
                <button onClick={send} className="rounded-2xl bg-red-600 px-4 py-2 text-sm font-semibold text-white">Send</button>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  )
}
