import './SidePanel.css'

function formatConversationDate(dateString) {
  if (!dateString) return 'Sin actividad'

  return new Intl.DateTimeFormat('es-GT', {
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  }).format(new Date(dateString))
}

function SidePanel({ conversations, activeConversationId, onSelectConversation, onNewConversation }) {
  return (
    <aside className="side-panel">
      <div className="side-panel__brand">
        <span className="side-panel__dot" />
        <div>
          <strong>StudyBot AI</strong>
          <p>Historial académico</p>
        </div>
      </div>

      <button className="side-panel__button" type="button" onClick={onNewConversation}>
        + Nueva conversación
      </button>

      <div className="side-panel__section">
        <div className="side-panel__header">
          <span>Conversaciones</span>
          <small>{conversations.length}</small>
        </div>

        <div className="side-panel__list">
          {conversations.length === 0 ? (
            <div className="side-panel__empty">
              Tus conversaciones aparecerán aquí cuando empieces a usar el chat.
            </div>
          ) : (
            conversations.map((conversation) => (
              <button
                key={conversation.conversation_id}
                type="button"
                className={`side-panel__item ${
                  activeConversationId === conversation.conversation_id ? 'is-active' : ''
                }`}
                onClick={() => onSelectConversation(conversation.conversation_id)}
              >
                <strong>{conversation.title}</strong>
                <span>{formatConversationDate(conversation.updated_at)}</span>
              </button>
            ))
          )}
        </div>
      </div>
    </aside>
  )
}

export default SidePanel
