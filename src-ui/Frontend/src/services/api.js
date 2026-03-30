const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...(options.token ? { Authorization: `Bearer ${options.token}` } : {}),
      ...options.headers,
    },
    method: options.method || 'GET',
    body: options.body ? JSON.stringify(options.body) : undefined,
  })

  const data = await response.json().catch(() => ({}))

  if (!response.ok) {
    throw new Error(data.detail || 'Ocurrió un error en la comunicación con el backend.')
  }

  return data
}

export function loginUser(payload) {
  return request('/auth/login', {
    method: 'POST',
    body: payload,
  })
}

export function registerUser(payload) {
  return request('/auth/register', {
    method: 'POST',
    body: payload,
  })
}

export function fetchConversations(token) {
  return request('/chat/conversations', {
    token,
  })
}

export function sendChatMessage(token, payload) {
  return request('/chat/completions', {
    method: 'POST',
    token,
    body: payload,
  })
}
