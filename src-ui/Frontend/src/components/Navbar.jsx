import './Navbar.css'

function buildInitials(name = '') {
  return name
    .split(' ')
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase() ?? '')
    .join('')
}

function Navbar({ title, subtitle, user, onLogout, onMenuOpen }) {
  return (
    <header className="navbar">
      <div className="navbar__heading">
        <p className="navbar__eyebrow">{subtitle}</p>
        <h1 className="navbar__title">{title}</h1>
      </div>

      <div className="navbar__actions">
        <div className="navbar__user">
          <div className="navbar__avatar" aria-hidden="true">
            {buildInitials(user?.full_name || user?.first_name || 'U')}
          </div>
          <div>
            <strong>{user?.full_name || 'Usuario'}</strong>
            <span>{user?.email}</span>
          </div>
        </div>

        <button className="navbar__logout" type="button" onClick={onLogout} title="Cerrar sesión">
          <svg viewBox="0 0 24 24" aria-hidden="true">
            <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
            <polyline points="16 17 21 12 16 7" />
            <line x1="21" y1="12" x2="9" y2="12" />
          </svg>
          <span className="navbar__logout-label">Cerrar sesión</span>
        </button>
      </div>

      <button
        className="navbar__menu-btn"
        type="button"
        onClick={onMenuOpen}
        aria-label="Abrir menú"
      >
        <span /><span /><span />
      </button>
    </header>
  )
}

export default Navbar
