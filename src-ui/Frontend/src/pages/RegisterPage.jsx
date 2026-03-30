import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import './RegisterPage.css'
import { useAuth } from '../hooks/useAuth.js'
import { registerUser } from '../services/api.js'

function RegisterPage() {
  const navigate = useNavigate()
  const { persistSession } = useAuth()
  const [form, setForm] = useState({
    first_name: '',
    last_name: '',
    student_id: '',
    email: '',
    password: '',
    confirm_password: '',
  })
  const [error, setError] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)

  const handleChange = (event) => {
    const { name, value } = event.target
    setForm((current) => ({ ...current, [name]: value }))
  }

  const handleSubmit = async (event) => {
    event.preventDefault()
    if (isSubmitting) return

    setError('')
    setIsSubmitting(true)

    try {
      const authResponse = await registerUser(form)
      persistSession(authResponse)
      navigate('/chat', { replace: true })
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'No fue posible registrarte.')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <main className="register-page route-shell">
      <section className="register-card">
        <div className="register-card__intro">
          <p className="register-card__eyebrow">Registro</p>
          <h1>Crea tu cuenta estudiantil</h1>
          <p>Necesitamos tus datos básicos para habilitar el acceso al chat institucional.</p>
        </div>

        <form className="register-card__form" onSubmit={handleSubmit}>
          <div className="register-card__grid">
            <label>
              <span>Nombre</span>
              <input
                name="first_name"
                value={form.first_name}
                onChange={handleChange}
                placeholder="Carlos"
              />
            </label>

            <label>
              <span>Apellido</span>
              <input
                name="last_name"
                value={form.last_name}
                onChange={handleChange}
                placeholder="Pérez"
              />
            </label>

            <label>
              <span>Carnet</span>
              <input
                name="student_id"
                value={form.student_id}
                onChange={handleChange}
                placeholder="20240001"
              />
            </label>

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
                placeholder="Mínimo 8 caracteres"
              />
            </label>

            <label>
              <span>Confirmación de contraseña</span>
              <input
                name="confirm_password"
                type="password"
                value={form.confirm_password}
                onChange={handleChange}
                placeholder="Repite tu contraseña"
              />
            </label>
          </div>

          {error && <div className="register-card__error">{error}</div>}

          <button type="submit" disabled={isSubmitting}>
            {isSubmitting ? 'Registrando...' : 'Crear cuenta'}
          </button>
        </form>

        <p className="register-card__footer">
          ¿Ya tienes cuenta? <Link to="/login">Volver al login</Link>
        </p>
      </section>
    </main>
  )
}

export default RegisterPage
