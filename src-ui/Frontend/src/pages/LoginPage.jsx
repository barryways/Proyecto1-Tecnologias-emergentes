import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import './LoginPage.css'
import { useAuth } from '../hooks/useAuth.js'
import { loginUser } from '../services/api.js'

function LoginPage() {
  const navigate = useNavigate()
  const { persistSession } = useAuth()
  const [form, setForm] = useState({
    email: '',
    password: '',
  })
  const [error, setError] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)

  const handleChange = (event) => {
    const { name, value } = event.target
    setForm((current) => ({ ...current, [name]: value }))
  }

  const submitWithPortal = async (portal) => {
    if (isSubmitting) return

    setError('')
    setIsSubmitting(true)

    try {
      const authResponse = await loginUser({ ...form, portal })
      persistSession(authResponse)
      navigate(portal === 'admin' ? '/admin' : '/chat', { replace: true })
    } catch (requestError) {
      setError(
        requestError instanceof Error ? requestError.message : 'No fue posible iniciar sesión.',
      )
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <main className="login-page route-shell">
      <section className="login-card">
        <div className="login-card__intro">
          <p className="login-card__eyebrow">Acceso</p>
          <h1>Inicia sesión en StudyBot</h1>
          <p>
            Usa tu correo y contraseña para entrar al chat del agente o al dashboard de
            administración.
          </p>
        </div>

        <div className="login-card__form">
          <label>
            <span>Correo institucional</span>
            <input
              name="email"
              type="email"
              value={form.email}
              onChange={handleChange}
              placeholder="tu.correo@universidad.edu"
            />
          </label>

          <label>
            <span>Contraseña</span>
            <input
              name="password"
              type="password"
              value={form.password}
              onChange={handleChange}
              placeholder="Ingresa tu contraseña"
            />
          </label>

          {error && <div className="login-card__error">{error}</div>}

          <div className="login-card__actions">
            <button type="button" onClick={() => submitWithPortal('chat')} disabled={isSubmitting}>
              {isSubmitting ? 'Validando...' : 'Entrar al chat'}
            </button>
            <button
              type="button"
              className="secondary"
              onClick={() => submitWithPortal('admin')}
              disabled={isSubmitting}
            >
              Dashboard admin
            </button>
          </div>
        </div>

        <p className="login-card__footer">
          ¿No tienes cuenta? <Link to="/register">Crear registro</Link>
        </p>
      </section>
    </main>
  )
}

export default LoginPage
