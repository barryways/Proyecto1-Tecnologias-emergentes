import { startTransition, useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import './ChatPage.css'
import Footer from '../components/Footer.jsx'
import Navbar from '../components/Navbar.jsx'
import SidePanel from '../components/SidePanel.jsx'
import { useAuth } from '../hooks/useAuth.js'
import { fetchConversations, sendChatMessage } from '../services/api.js'
import { clearConversationCache, loadConversationCache, saveConversationCache } from '../services/conversationStorage.js'

function buildWelcomeMessage(firstName = 'estudiante') {
  return {
    role: 'assistant',
    content: `Hola ${firstName}, soy StudyBot. Tus mensajes se están enviando al backend en Python para gestionar la conversación.`,
    timestamp: new Date().toISOString(),
  }
}

function sortConversations(conversations) {
  return [...conversations].sort(
    (left, right) => new Date(right.updated_at).getTime() - new Date(left.updated_at).getTime(),
  )
}

function upsertConversation(conversations, nextConversation) {
  const filtered = conversations.filter(
    (conversation) => conversation.conversation_id !== nextConversation.conversation_id,
  )
  return sortConversations([nextConversation, ...filtered])
}

function ChatPage() {
  const navigate = useNavigate()
  const { user, token, logout } = useAuth()
  const [conversations, setConversations] = useState([])
  const [activeConversationId, setActiveConversationId] = useState(null)
  const [draftMessages, setDraftMessages] = useState(() => [buildWelcomeMessage(user?.first_name)])
  const [input, setInput] = useState('')
  const [error, setError] = useState('')
  const [isLoading, setIsLoading] = useState(false)

  useEffect(() => {
    const cachedConversations = loadConversationCache(user?.email)
    if (cachedConversations.length > 0) {
      setConversations(cachedConversations)
      setActiveConversationId(cachedConversations[0].conversation_id)
    }

    let ignore = false

    const loadRemoteConversations = async () => {
      try {
        const remoteConversations = await fetchConversations(token)
        if (ignore) return

        startTransition(() => {
          setConversations(remoteConversations)
          saveConversationCache(user?.email, remoteConversations)

          if (remoteConversations.length > 0) {
            setActiveConversationId((current) =>
              current && remoteConversations.some((item) => item.conversation_id === current)
                ? current
                : remoteConversations[0].conversation_id,
            )
          }
        })
      } catch (requestError) {
        if (!ignore) {
          setError(
            requestError instanceof Error
              ? requestError.message
              : 'No fue posible cargar las conversaciones.',
          )
        }
      }
    }

    loadRemoteConversations()

    return () => {
      ignore = true
    }
  }, [token, user?.email])

  const activeConversation = conversations.find(
    (conversation) => conversation.conversation_id === activeConversationId,
  )
  const visibleMessages = activeConversation?.messages ?? draftMessages

  const handleLogout = () => {
    clearConversationCache(user?.email)
    logout()
    navigate('/login', { replace: true })
  }

  const handleNewConversation = () => {
    setActiveConversationId(null)
    setDraftMessages([buildWelcomeMessage(user?.first_name)])
    setInput('')
    setError('')
  }

  const handleSelectConversation = (conversationId) => {
    setActiveConversationId(conversationId)
    setError('')
  }

  const handleSend = async () => {
    const trimmed = input.trim()
    if (!trimmed || isLoading) return

    const baseMessages = activeConversation?.messages ?? draftMessages
    const nextMessages = [
      ...baseMessages,
      {
        role: 'user',
        content: trimmed,
        timestamp: new Date().toISOString(),
      },
    ]

    setError('')
    setInput('')
    setIsLoading(true)

    if (activeConversation) {
      setConversations((current) =>
        current.map((conversation) =>
          conversation.conversation_id === activeConversation.conversation_id
            ? {
                ...conversation,
                messages: nextMessages,
                updated_at: new Date().toISOString(),
                message_count: nextMessages.length,
              }
            : conversation,
        ),
      )
    } else {
      setDraftMessages(nextMessages)
    }

    try {
      const response = await sendChatMessage(token, {
        conversation_id: activeConversation?.conversation_id ?? null,
        message: trimmed,
        history: nextMessages,
      })

      const syncedConversation = response.conversation

      startTransition(() => {
        setConversations((current) => {
          const updatedConversations = upsertConversation(current, syncedConversation)
          saveConversationCache(user?.email, updatedConversations)
          return updatedConversations
        })
        setActiveConversationId(syncedConversation.conversation_id)
        setDraftMessages([buildWelcomeMessage(user?.first_name)])
      })
    } catch (requestError) {
      if (activeConversation) {
        setConversations((current) =>
          current.map((conversation) =>
            conversation.conversation_id === activeConversation.conversation_id
              ? {
                  ...conversation,
                  messages: baseMessages,
                  message_count: baseMessages.length,
                }
              : conversation,
          ),
        )
      } else {
        setDraftMessages(baseMessages)
      }

      setInput(trimmed)
      setError(
        requestError instanceof Error
          ? requestError.message
          : 'No fue posible enviar el mensaje al backend.',
      )
    } finally {
      setIsLoading(false)
    }
  }

  const handleKeyDown = (event) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="chat-page route-shell">
      <div className="chat-page__shell">
        <Navbar
          title="Chat del Agente"
          subtitle="Sesión estudiantil"
          user={user}
          onLogout={handleLogout}
        />

        <div className="chat-page__layout">
          <SidePanel
            conversations={conversations}
            activeConversationId={activeConversationId}
            onSelectConversation={handleSelectConversation}
            onNewConversation={handleNewConversation}
          />

          <section className="chat-page__panel">
            <div className="chat-page__status">
              <div>
                <strong>Canal conectado</strong>
                <span>Las consultas se envían por HTTP al backend de `src/api-ia`.</span>
              </div>
            </div>

            <div className="chat-page__messages">
              {visibleMessages.map((message, index) => (
                <article key={`${message.timestamp}-${index}`} className={`chat-bubble ${message.role}`}>
                  <span className="chat-bubble__role">
                    {message.role === 'assistant' ? 'Asistente' : 'Tú'}
                  </span>
                  <p>{message.content}</p>
                </article>
              ))}

              {isLoading && (
                <article className="chat-bubble assistant is-loading">
                  <span className="chat-bubble__role">Asistente</span>
                  <p>Generando respuesta desde el backend...</p>
                </article>
              )}
            </div>

            <div className="chat-page__composer">
              {error && <div className="chat-page__error">{error}</div>}

              <div className="chat-page__composer-row">
                <textarea
                  rows={1}
                  value={input}
                  onChange={(event) => setInput(event.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder="Escribe una consulta para el agente..."
                />
                <button type="button" onClick={handleSend} disabled={isLoading || !input.trim()}>
                  {isLoading ? '...' : 'Enviar'}
                </button>
              </div>
            </div>
          </section>
        </div>

        <Footer />
      </div>
    </div>
  )
}

export default ChatPage
