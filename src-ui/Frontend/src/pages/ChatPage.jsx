import { useEffect, useRef, useState } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { useNavigate } from 'react-router-dom'
import './ChatPage.css'
import Footer from '../components/Footer.jsx'
import Navbar from '../components/Navbar.jsx'
import SidePanel from '../components/SidePanel.jsx'
import { useAudioRecorder } from '../hooks/useAudioRecorder.js'
import { useAuth } from '../hooks/useAuth.js'
import { useSpeech } from '../hooks/useSpeech.js'
import { fetchConversations, sendChatMessage, transcribeAudio } from '../services/api.js'

function buildWelcomeMessage(firstName = 'estudiante') {
  return {
    role: 'assistant',
    content: `Hola ${firstName}, soy StudyBot. En que duda puedo ayudarte hoy.`,
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

function buildPendingAssistantMessage() {
  return {
    role: 'assistant',
    content: '',
    timestamp: `${new Date().toISOString()}-pending`,
    isPending: true,
  }
}

function buildFallbackConversation(serverConversation, nextMessages, assistantReply) {
  const remoteMessages = Array.isArray(serverConversation?.messages)
    ? serverConversation.messages.filter((message) => !message?.isPending)
    : []
  const fallbackMessages = [...nextMessages, assistantReply]
  const resolvedMessages =
    remoteMessages.length >= fallbackMessages.length ? remoteMessages : fallbackMessages

  return {
    ...serverConversation,
    messages: resolvedMessages,
    message_count: resolvedMessages.length,
    updated_at: serverConversation?.updated_at ?? assistantReply.timestamp,
  }
}

function VoiceIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path d="M12 15.5a3.5 3.5 0 0 0 3.5-3.5V7a3.5 3.5 0 1 0-7 0v5a3.5 3.5 0 0 0 3.5 3.5Z" />
      <path d="M18 11.5a6 6 0 0 1-12 0" />
      <path d="M12 17.5v4" />
      <path d="M8.5 21.5h7" />
    </svg>
  )
}

function ChatPage() {
  const navigate = useNavigate()
  const { user, token, logout } = useAuth()
  const dictationBaseRef = useRef('')
  const messagesEndRef = useRef(null)
  const [conversations, setConversations] = useState([])
  const [activeConversationId, setActiveConversationId] = useState(null)
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [draftMessages, setDraftMessages] = useState(() => [buildWelcomeMessage(user?.first_name)])
  const [input, setInput] = useState('')
  const [error, setError] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [isTranscribing, setIsTranscribing] = useState(false)
  const { isRecording, isRecordingSupported, startRecording, stopRecording, cancelRecording } =
    useAudioRecorder()
  const {
    speakingMessageId,
    isSpeechSynthesisSupported,
    speakMessage,
    stopSpeaking,
    stopListening,
  } = useSpeech()

  useEffect(() => {
    let ignore = false

    const loadRemoteConversations = async () => {
      try {
        const remoteConversations = await fetchConversations(token)
        if (ignore) return

        setConversations(remoteConversations)

        if (remoteConversations.length > 0) {
          setActiveConversationId((current) =>
            current && remoteConversations.some((item) => item.conversation_id === current)
              ? current
              : remoteConversations[0].conversation_id,
          )
        }
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

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' })
  }, [visibleMessages, isLoading])

  const handleLogout = () => {
    cancelRecording()
    stopListening()
    stopSpeaking()
    logout()
    navigate('/login', { replace: true })
  }

  const handleNewConversation = () => {
    cancelRecording()
    stopListening()
    stopSpeaking()
    setActiveConversationId(null)
    setDraftMessages([buildWelcomeMessage(user?.first_name)])
    setInput('')
    setError('')
  }

  const handleSelectConversation = (conversationId) => {
    cancelRecording()
    stopListening()
    stopSpeaking()
    setActiveConversationId(conversationId)
    setError('')
  }

  const handleSend = async () => {
    const trimmed = input.trim()
    if (!trimmed || isLoading) return

    cancelRecording()
    stopListening()

    const baseMessages = activeConversation?.messages ?? draftMessages
    const nextMessages = [
      ...baseMessages,
      {
        role: 'user',
        content: trimmed,
        timestamp: new Date().toISOString(),
      },
    ]
    const optimisticMessages = [...nextMessages, buildPendingAssistantMessage()]

    setError('')
    setInput('')
    setIsLoading(true)

    if (activeConversation) {
      setConversations((current) =>
        current.map((conversation) =>
          conversation.conversation_id === activeConversation.conversation_id
            ? {
                ...conversation,
                messages: optimisticMessages,
                updated_at: new Date().toISOString(),
                message_count: optimisticMessages.length,
              }
            : conversation,
        ),
      )
    } else {
      setDraftMessages(optimisticMessages)
    }

    try {
      const response = await sendChatMessage(token, {
        conversation_id: activeConversation?.conversation_id ?? null,
        message: trimmed,
        history: nextMessages,
      })

      const assistantReply = {
        role: 'assistant',
        content: response.content,
        timestamp: new Date().toISOString(),
      }
      const syncedConversation = buildFallbackConversation(
        response.conversation,
        nextMessages,
        assistantReply,
      )

      setConversations((current) => upsertConversation(current, syncedConversation))
      setActiveConversationId(syncedConversation.conversation_id)
      setDraftMessages([buildWelcomeMessage(user?.first_name)])
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

  const handleSpeakMessage = (message, index) => {
    const result = speakMessage(
      `${activeConversationId || 'draft'}-${message.timestamp || index}-${message.role}`,
      message.content,
    )

    if (result?.ok) {
      setError('')
      return
    }

    if (result?.reason) {
      setError(result.reason)
    }
  }

  const transcribeRecordedAudio = async (audioBlob) => {
    if (!audioBlob) {
      setError('No se pudo recuperar el audio grabado.')
      return false
    }

    try {
      setError('')
      setIsTranscribing(true)
      const response = await transcribeAudio(token, audioBlob)
      const baseText = dictationBaseRef.current || ''
      const nextText = `${baseText}${response.text}`.trim()
      setInput(nextText)
      dictationBaseRef.current = nextText ? `${nextText} ` : ''
      return true
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : 'No fue posible transcribir el audio grabado.',
      )
      return false
    } finally {
      setIsTranscribing(false)
    }
  }

  const startBackendDictation = async () => {
    try {
      setError('')
      stopListening()
      dictationBaseRef.current = input.trim() ? `${input.trim()} ` : ''
      await startRecording({
        autoStop: true,
        onAutoStop: (audioBlob) => {
          void transcribeRecordedAudio(audioBlob)
        },
      })
      return true
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : 'No fue posible iniciar la grabación de audio.',
      )
      return false
    }
  }

  const handleVoiceInput = () => {
    const run = async () => {
      if (isTranscribing) {
        return
      }

      if (isRecording) {
        const audioBlob = await stopRecording()
        await transcribeRecordedAudio(audioBlob)
        return
      }

      await startBackendDictation()
    }

    run()
  }

  return (
    <div className="chat-page route-shell">
      <div className="chat-page__shell">
        <Navbar
          title="Chat del Agente"
          subtitle="Sesión estudiantil"
          user={user}
          onLogout={handleLogout}
          onMenuOpen={() => setSidebarOpen(true)}
        />

        <div className="chat-page__layout">
          <SidePanel
            conversations={conversations}
            activeConversationId={activeConversationId}
            onSelectConversation={handleSelectConversation}
            onNewConversation={handleNewConversation}
            isOpen={sidebarOpen}
            onClose={() => setSidebarOpen(false)}
            user={user}
            onLogout={handleLogout}
          />

          <section className="chat-page__panel">
            <div className="chat-page__status">
              <div>
                <strong>Canal conectado</strong>
              </div>
              <div className="chat-page__voice-summary">
                <span>{isSpeechSynthesisSupported ? 'Audio activo' : 'Audio no disponible'}</span>
                <span>{isRecordingSupported ? 'Dictado por voz activo' : 'Dictado no disponible'}</span>
              </div>
            </div>

            <div className="chat-page__messages">
              {visibleMessages.map((message, index) => (
                <article key={`${message.timestamp}-${index}`} className={`chat-bubble ${message.role}`}>
                  <div className="chat-bubble__header">
                    <span className="chat-bubble__role">
                      {message.role === 'assistant' ? 'Asistente' : 'Tú'}
                    </span>
                    <button
                      type="button"
                      className={`chat-bubble__voice-button ${
                        speakingMessageId ===
                        `${activeConversationId || 'draft'}-${message.timestamp || index}-${message.role}`
                          ? 'is-speaking'
                          : ''
                      }`}
                      onClick={() => handleSpeakMessage(message, index)}
                      disabled={!isSpeechSynthesisSupported || message.isPending}
                      title="Reproducir mensaje"
                    >
                      <VoiceIcon />
                    </button>
                  </div>
                  {message.isPending ? (
                    <div className="chat-bubble__typing" aria-live="polite">
                      <span />
                      <span />
                      <span />
                    </div>
                  ) : (
                    <div className="chat-bubble__content">
                      {message.role === 'assistant' ? (
                        <ReactMarkdown
                          remarkPlugins={[remarkGfm]}
                          components={{
                            a: ({ ...props }) => (
                              <a {...props} target="_blank" rel="noreferrer noopener" />
                            ),
                          }}
                        >
                          {message.content}
                        </ReactMarkdown>
                      ) : (
                        <p>{message.content}</p>
                      )}
                    </div>
                  )}
                </article>
              ))}
              <div ref={messagesEndRef} />
            </div>

            <div className="chat-page__composer">
              {error && <div className="chat-page__error">{error}</div>}

              <div className="chat-page__composer-row">
                <textarea
                  rows={1}
                  value={input}
                  onChange={(event) => {
                    setInput(event.target.value)
                    dictationBaseRef.current = event.target.value.trim()
                      ? `${event.target.value.trim()} `
                      : ''
                  }}
                  onKeyDown={handleKeyDown}
                  placeholder="Escribe una consulta para el agente..."
                />
                <button
                  type="button"
                  className={`chat-page__voice-input ${isRecording ? 'is-listening' : ''}`}
                  onClick={handleVoiceInput}
                  disabled={!isRecordingSupported || isTranscribing}
                  title={
                    isRecording
                      ? 'Detener grabacion y transcribir'
                      : 'Hablar para dictar al mensaje'
                  }
                >
                  <VoiceIcon />
                </button>
                <button type="button" className="chat-page__send-btn" onClick={handleSend} disabled={isLoading || !input.trim()}>
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
