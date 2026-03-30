function buildConversationKey(email) {
  return `studybot.conversations.${email || 'anonymous'}`
}

export function loadConversationCache(email) {
  const rawValue = localStorage.getItem(buildConversationKey(email))
  if (!rawValue) return []

  try {
    const parsed = JSON.parse(rawValue)
    return Array.isArray(parsed) ? parsed : []
  } catch {
    localStorage.removeItem(buildConversationKey(email))
    return []
  }
}

export function saveConversationCache(email, conversations) {
  localStorage.setItem(buildConversationKey(email), JSON.stringify(conversations))
}

export function clearConversationCache(email) {
  localStorage.removeItem(buildConversationKey(email))
}
