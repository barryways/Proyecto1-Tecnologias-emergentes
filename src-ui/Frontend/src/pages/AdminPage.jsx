import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import './AdminPage.css'
import Footer from '../components/Footer.jsx'
import Navbar from '../components/Navbar.jsx'
import { useAuth } from '../hooks/useAuth.js'
import { fetchUsuarios, fetchTokens } from '../services/api.js'

function StatCard({ label, value, highlight }) {
  return (
    <div className={`dash-stat${highlight ? ' dash-stat--highlight' : ''}`}>
      <span className="dash-stat__label">{label}</span>
      <span className="dash-stat__value">{value}</span>
    </div>
  )
}

function AdminPage() {
  const navigate = useNavigate()
  const { user, session, logout } = useAuth()
  const token = session?.token

  const [usuarios, setUsuarios] = useState([])
  const [selectedId, setSelectedId] = useState('')
  const [consumo, setConsumo] = useState(null)
  const [loadingUsers, setLoadingUsers] = useState(true)
  const [loadingConsumo, setLoadingConsumo] = useState(false)
  const [error, setError] = useState(null)

  const handleLogout = () => {
    logout()
    navigate('/login', { replace: true })
  }

  useEffect(() => {
    setLoadingUsers(true)
    fetchUsuarios(token)
      .then(data => setUsuarios(data))
      .catch(() => setError('No se pudieron cargar los usuarios.'))
      .finally(() => setLoadingUsers(false))
  }, [token])

  useEffect(() => {
    if (!selectedId) return
    setLoadingConsumo(true)
    setConsumo(null)
    fetchTokens(token, selectedId)
      .then(data => setConsumo(data))
      .catch(() => setError('No se pudo cargar el consumo del usuario.'))
      .finally(() => setLoadingConsumo(false))
  }, [token, selectedId])

  const selectedUser = usuarios.find(u => String(u.id_usuario) === String(selectedId))

  return (
    <div className="admin-page route-shell">
      <div className="admin-page__shell">
        <Navbar
          title="Dashboard de Administración"
          subtitle="Panel interno"
          user={user}
          onLogout={handleLogout}
        />

        <section className="dash-body">
          {/* ── SELECTOR DE USUARIO ── */}
          <div className="dash-selector-block">
            <h2 className="dash-section-title">Seleccionar usuario</h2>

            {loadingUsers ? (
              <p className="dash-loading">Cargando usuarios…</p>
            ) : (
              <div className="dash-selector-wrap">
                <select
                  className="dash-select"
                  value={selectedId}
                  onChange={e => { setSelectedId(e.target.value); setError(null) }}
                >
                  <option value="">-- Elige un usuario --</option>
                  {usuarios.map(u => (
                    <option key={u.id_usuario} value={u.id_usuario}>
                      #{u.id_usuario} · {u.nombre} {u.apellido}
                    </option>
                  ))}
                </select>

                {selectedUser && (
                  <span className="dash-selected-badge">
                    Usuario activo: <strong>{selectedUser.nombre} {selectedUser.apellido}</strong>
                  </span>
                )}
              </div>
            )}
          </div>

          {/* ── ERROR ── */}
          {error && <p className="dash-error">{error}</p>}

          {/* ── CONSUMO ── */}
          {!selectedId && !loadingUsers && (
            <div className="dash-empty">
              <p>Selecciona un usuario para ver su consumo.</p>
            </div>
          )}

          {loadingConsumo && <p className="dash-loading">Cargando consumo…</p>}

          {consumo && !loadingConsumo && (
            <>
              {/* Resumen en cards */}
              <div className="dash-section">
                <h2 className="dash-section-title">Resumen</h2>
                <div className="dash-stats-grid">
                  <StatCard label="Estudiante" value={consumo.nombre_completo} highlight />
                  <StatCard
                    label="Costo total"
                    value={`$${parseFloat(consumo.resumen.costo_total).toFixed(6)} USD`}
                  />
                  <StatCard
                    label="Tokens totales"
                    value={consumo.resumen.tokens_totales.toLocaleString()}
                  />
                  <StatCard
                    label="Total consultas"
                    value={consumo.resumen.total_consultas}
                  />
                </div>
                <p className="dash-last-seen">
                  Último consumo: <strong>{consumo.ultimo_consumo ?? '—'}</strong>
                </p>
              </div>

              {/* Tabla de últimas consultas */}
              <div className="dash-section">
                <h2 className="dash-section-title">Últimas consultas</h2>

                {consumo.ultimas_consultas?.length === 0 ? (
                  <p className="dash-empty-inline">Sin consultas registradas.</p>
                ) : (
                  <div className="dash-table-wrap">
                    <table className="dash-table">
                      <thead>
                        <tr>
                          <th>Fecha</th>
                          <th>Modelo</th>
                          <th>T. entrada</th>
                          <th>T. salida</th>
                          <th>T. total</th>
                          <th>Costo entrada</th>
                          <th>Costo salida</th>
                          <th>Costo total</th>
                        </tr>
                      </thead>
                      <tbody>
                        {consumo.ultimas_consultas.map((q, i) => (
                          <tr key={i}>
                            <td data-label="Fecha">{q.fec_consumo}</td>
                            <td data-label="Modelo">
                              <span className="dash-model-tag">{q.modelo}</span>
                            </td>
                            <td data-label="T. entrada">{q.tokens_entrada}</td>
                            <td data-label="T. salida">{q.tokens_salida}</td>
                            <td data-label="T. total"><strong>{q.tokens_totales}</strong></td>
                            <td data-label="Costo entrada">${parseFloat(q.costo_entrada).toFixed(6)}</td>
                            <td data-label="Costo salida">${parseFloat(q.costo_salida).toFixed(6)}</td>
                            <td data-label="Costo total">
                              <strong>${parseFloat(q.costo_total).toFixed(6)}</strong>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            </>
          )}
        </section>

        <Footer text="StudyBot AI · Área administrativa" />
      </div>
    </div>
  )
}

export default AdminPage