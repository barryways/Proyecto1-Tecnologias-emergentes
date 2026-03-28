import { useMemo, useRef, useState } from 'react'
import './App.css'

const INITIAL_ASSISTANT_MESSAGE = {
  id: crypto.randomUUID(),
  role: 'assistant',
  content:
    'Hola, soy StudyBot. Puedo ayudarte con tareas, resúmenes, dudas de programación y preparación para exámenes.',
}

function App() {
  const [messages, setMessages] = useState([INITIAL_ASSISTANT_MESSAGE])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')
  const controllerRef = useRef(null)

  const apiUrl = useMemo(
    () => import.meta.env.VITE_CHAT_API_URL || 'http://localhost:3000/api/chat',
    [],
  )

  const getAssistantReply = async (message, history, signal) => {
    const response = await fetch(apiUrl, {
      method: 'POST',
      signal,
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        message,
        history,
      }),
    })

    if (!response.ok) {
      throw new Error(`Error ${response.status}: no fue posible obtener respuesta.`)
    }

    const data = await response.json()
    return data.reply || data.response || data.message || data.answer || ''
  }

  const handleSend = async () => {
    const trimmed = input.trim()
    if (!trimmed || isLoading) return

    setError('')
    setInput('')

    const userMessage = {
      id: crypto.randomUUID(),
      role: 'user',
      content: trimmed,
    }

    const nextHistory = [...messages, userMessage].map(({ role, content }) => ({
      role,
      content,
    }))

    setMessages((prev) => [...prev, userMessage])
    setIsLoading(true)
    const controller = new AbortController()
    controllerRef.current = controller

    try {
      const reply = await getAssistantReply(trimmed, nextHistory, controller.signal)
      const safeReply =
        typeof reply === 'string' && reply.trim().length > 0
          ? reply
          : 'No se recibió contenido en la respuesta del backend.'

      setMessages((prev) => [
        ...prev,
        {
          id: crypto.randomUUID(),
          role: 'assistant',
          content: safeReply,
        },
      ])
    } catch (requestError) {
      if (requestError instanceof Error && requestError.name === 'AbortError') {
        return
      }
      setError(
        requestError instanceof Error
          ? requestError.message
          : 'Ocurrió un error al conectar con el backend.',
      )
    } finally {
      setIsLoading(false)
      controllerRef.current = null
    }
  }

  const handleKeyDown = (event) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault()
      handleSend()
    }
  }

  const handleNewChat = () => {
    if (controllerRef.current) {
      controllerRef.current.abort()
      controllerRef.current = null
    }

    setMessages([
      {
        ...INITIAL_ASSISTANT_MESSAGE,
        id: crypto.randomUUID(),
      },
    ])
    setInput('')
    setError('')
    setIsLoading(false)
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <span className="brand-dot" />
          <div>
            <h1>StudyBot AI</h1>
            <p>Asistente Estudiantil</p>
          </div>
        </div>
        <button className="new-chat-btn" type="button" onClick={handleNewChat}>
          + Nuevo chat
        </button>
        <div className="sidebar-hint">
          <p>Conecta tu backend configurando:</p>
          <code>VITE_CHAT_API_URL</code>
        </div>
      </aside>

      <main className="chat-panel">
        <header className="chat-header">
          <p>Modo Tutor</p>
          <span>{apiUrl}</span>
        </header>

        <section className="messages">
          {messages.map((message) => (
            <article key={message.id} className={`message ${message.role}`}>
              <div className="message-role">
                {message.role === 'assistant' ? 'IA' : 'Tú'}
              </div>
              <p>{message.content}</p>
            </article>
          ))}
          {isLoading && (
            <article className="message assistant loading">
              <div className="message-role">IA</div>
              <p>Escribiendo...</p>
            </article>
          )}
        </section>

        <footer className="composer">
          {error && <div className="error-box">{error}</div>}
          <div className="composer-row">
            <textarea
              placeholder="Escribe tu pregunta de estudio..."
              value={input}
              onChange={(event) => setInput(event.target.value)}
              onKeyDown={handleKeyDown}
              rows={1}
            />
            <button type="button" onClick={handleSend} disabled={isLoading || !input.trim()}>
              {isLoading ? '...' : 'Enviar'}
            </button>
          </div>
        </footer>
      </main>
    </div>
  )
}

export default App
