import './Navbar.css'

function buildInitials(name = '') {
  return name
    .split(' ')
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase() ?? '')
    .join('')
}

function Navbar({ title, subtitle, user, onLogout }) {
  return (
    <header className="navbar">
      <div>
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

        <button className="navbar__logout" type="button" onClick={onLogout}>
          Cerrar sesión
        </button>
      </div>
    </header>
  )
}

export default Navbar
