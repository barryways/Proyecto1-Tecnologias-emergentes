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
  const [showPassword, setShowPassword] = useState(false)

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
      <p className="login-page__logo">StudyBot</p>

      <section className="login-card">
        <div className="login-card__intro">
          <h1>Inicia sesión</h1>
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
            <div className="login-card__input-wrap">
              <input
                name="password"
                type={showPassword ? 'text' : 'password'}
                value={form.password}
                onChange={handleChange}
                placeholder="Ingresa tu contraseña"
              />
              <button
                type="button"
                className="login-card__toggle-pw"
                onClick={() => setShowPassword((v) => !v)}
                aria-label={showPassword ? 'Ocultar contraseña' : 'Mostrar contraseña'}
              >
                {showPassword ? (
                  <svg viewBox="0 0 24 24" aria-hidden="true">
                    <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94" />
                    <path d="M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19" />
                    <line x1="1" y1="1" x2="23" y2="23" />
                  </svg>
                ) : (
                  <svg viewBox="0 0 24 24" aria-hidden="true">
                    <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
                    <circle cx="12" cy="12" r="3" />
                  </svg>
                )}
              </button>
            </div>
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

      <p className="login-page__copyright">
        &copy; {new Date().getFullYear()} StudyBot. Todos los derechos reservados.
      </p>
    </main>
  )
}

export default LoginPage
