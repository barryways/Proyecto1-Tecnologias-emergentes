import { useNavigate } from 'react-router-dom'
import './AdminPage.css'
import Footer from '../components/Footer.jsx'
import Navbar from '../components/Navbar.jsx'
import { useAuth } from '../hooks/useAuth.js'

function AdminPage() {
  const navigate = useNavigate()
  const { user, logout } = useAuth()

  const handleLogout = () => {
    logout()
    navigate('/login', { replace: true })
  }

  return (
    <div className="admin-page route-shell">
      <div className="admin-page__shell">
        <Navbar
          title="Dashboard de Administración"
          subtitle="Panel interno"
          user={user}
          onLogout={handleLogout}
        />

        <section className="admin-page__content">
          <div className="admin-page__card">
            <p className="admin-page__eyebrow">Próximamente</p>
            <h2>Dashboard vacío por ahora</h2>
            <button type="button" onClick={handleLogout}>
              Cerrar sesión
            </button>
          </div>
        </section>

        <Footer text="StudyBot AI · Área administrativa" />
      </div>
    </div>
  )
}

export default AdminPage
