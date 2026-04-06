import './SidePanel.css'

function buildInitials(name = '') {
  return name
    .split(' ')
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase() ?? '')
    .join('')
}

function formatConversationDate(dateString) {
  if (!dateString) return 'Sin actividad'

  return new Intl.DateTimeFormat('es-GT', {
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  }).format(new Date(dateString))
}

function SidePanel({ conversations, activeConversationId, onSelectConversation, onNewConversation, isOpen, onClose, user, onLogout }) {
  const handleSelect = (id) => {
    onSelectConversation(id)
    onClose?.()
  }

  const handleNew = () => {
    onNewConversation()
    onClose?.()
  }

  return (
    <>
      {isOpen && <div className="side-panel__backdrop" onClick={onClose} />}
      <aside className={`side-panel${isOpen ? ' is-open' : ''}`}>

        <div className="side-panel__drawer-header">
          <div className="side-panel__brand">
            <span className="side-panel__dot" />
            <div>
              <strong>StudyBot AI</strong>
              <p>Historial académico</p>
            </div>
          </div>
          <button className="side-panel__close-btn" type="button" onClick={onClose} aria-label="Cerrar menú">
            ✕
          </button>
        </div>

        <div className="side-panel__user-card">
          <div className="side-panel__avatar">
            {buildInitials(user?.full_name || user?.first_name || 'U')}
          </div>
          <div className="side-panel__user-info">
            <strong>{user?.full_name || 'Usuario'}</strong>
            <span>{user?.email}</span>
          </div>
        </div>

        <button className="side-panel__logout-btn" type="button" onClick={onLogout}>
          <svg viewBox="0 0 24 24" aria-hidden="true">
            <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
            <polyline points="16 17 21 12 16 7" />
            <line x1="21" y1="12" x2="9" y2="12" />
          </svg>
          Cerrar sesión
        </button>

        <button className="side-panel__button" type="button" onClick={handleNew}>
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
                  onClick={() => handleSelect(conversation.conversation_id)}
                >
                  <strong>{conversation.title}</strong>
                  <span>{formatConversationDate(conversation.updated_at)}</span>
                </button>
              ))
            )}
          </div>
        </div>
      </aside>
    </>
  )
}

export default SidePanel
