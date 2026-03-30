const SESSION_STORAGE_KEY = 'studybot.session'

function isExpired(expiresAt) {
  return !expiresAt || Number.isNaN(new Date(expiresAt).getTime()) || new Date(expiresAt) <= new Date()
}

export function loadStoredSession() {
  const rawValue = localStorage.getItem(SESSION_STORAGE_KEY)
  if (!rawValue) return null

  try {
    const parsed = JSON.parse(rawValue)
    if (isExpired(parsed.expiresAt)) {
      localStorage.removeItem(SESSION_STORAGE_KEY)
      return null
    }

    return parsed
  } catch {
    localStorage.removeItem(SESSION_STORAGE_KEY)
    return null
  }
}

export function saveStoredSession(authResponse) {
  const nextSession = {
    accessToken: authResponse.access_token,
    expiresAt: authResponse.expires_at,
    portal: authResponse.portal,
    user: authResponse.user,
  }

  localStorage.setItem(SESSION_STORAGE_KEY, JSON.stringify(nextSession))
  return nextSession
}

export function clearStoredSession() {
  localStorage.removeItem(SESSION_STORAGE_KEY)
}
