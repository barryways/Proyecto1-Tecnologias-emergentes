import { useEffect, useRef, useState } from 'react'

function getSpeechRecognition() {
  if (typeof window === 'undefined') return null

  return window.SpeechRecognition || window.webkitSpeechRecognition || null
}

function getRecognitionLanguage() {
  if (typeof navigator === 'undefined') return 'es-ES'

  const preferredLanguage = navigator.language?.toLowerCase() || ''
  if (preferredLanguage.startsWith('es-gt')) {
    return 'es-GT'
  }
  if (preferredLanguage.startsWith('es')) {
    return navigator.language
  }

  return 'es-GT'
}

function mapRecognitionError(errorCode) {
  switch (errorCode) {
    case 'not-allowed':
      return 'Debes permitir el uso del micrófono en el navegador para dictar mensajes.'
    case 'service-not-allowed':
      return 'El navegador bloqueó el servicio de reconocimiento. Prueba en Chrome o Edge y revisa los permisos del sitio.'
    case 'audio-capture':
      return 'No se encontró un micrófono disponible o el sistema no puede acceder a él.'
    case 'no-speech':
      return 'No se detectó voz. Intenta hablar más cerca del micrófono.'
    case 'network':
      return 'El reconocimiento de voz del navegador falló por red.'
    case 'language-not-supported':
      return 'El navegador no tiene soporte local para el idioma del dictado.'
    case 'language-unavailable':
      return 'El paquete local de idioma para dictado no está disponible todavía.'
    case 'aborted':
      return 'El dictado se canceló antes de completarse.'
    default:
      return `No fue posible reconocer tu voz en este momento. Código: ${errorCode || 'desconocido'}.`
  }
}

function createRecognitionInstance() {
  const SpeechRecognitionCtor = getSpeechRecognition()
  if (!SpeechRecognitionCtor) return { recognition: null, SpeechRecognitionCtor: null }

  const recognition = new SpeechRecognitionCtor()
  recognition.lang = getRecognitionLanguage()
  recognition.interimResults = true
  recognition.continuous = false
  recognition.maxAlternatives = 1
  return { recognition, SpeechRecognitionCtor }
}

async function ensureOnDeviceRecognition(SpeechRecognitionCtor, recognition) {
  if (!recognition || !SpeechRecognitionCtor) {
    return { ok: false, reason: 'Tu navegador no soporta reconocimiento de voz.' }
  }

  if (!('processLocally' in recognition)) {
    return {
      ok: false,
      reason: 'Este navegador no soporta dictado local en el dispositivo.',
    }
  }

  recognition.processLocally = true

  if (typeof SpeechRecognitionCtor.available !== 'function') {
    return { ok: true }
  }

  try {
    const availability = await SpeechRecognitionCtor.available({
      langs: [recognition.lang],
      processLocally: true,
    })

    if (availability === 'available') {
      return { ok: true }
    }

    if (availability === 'downloadable' && typeof SpeechRecognitionCtor.install === 'function') {
      const installed = await SpeechRecognitionCtor.install({
        langs: [recognition.lang],
        processLocally: true,
      })

      if (installed) {
        return { ok: true }
      }
    }

    if (availability === 'downloading') {
      return {
        ok: false,
        reason: 'El navegador todavía está descargando el paquete de voz local.',
      }
    }

    return {
      ok: false,
      reason: 'El navegador no tiene disponible dictado local para este idioma.',
    }
  } catch (error) {
    return {
      ok: false,
      reason:
        error instanceof Error
          ? error.message
          : 'No fue posible preparar el dictado local en este navegador.',
    }
  }
}

function pickVoice(voices) {
  return (
    voices.find((voice) => voice.lang?.toLowerCase().startsWith('es-gt')) ||
    voices.find((voice) => voice.lang?.toLowerCase().startsWith('es')) ||
    null
  )
}

export function useSpeech() {
  const recognitionRef = useRef(null)
  const [isListening, setIsListening] = useState(false)
  const [speakingMessageId, setSpeakingMessageId] = useState('')
  const [isSpeechRecognitionSupported] = useState(() => Boolean(getSpeechRecognition()))
  const [isSpeechSynthesisSupported] = useState(
    () => typeof window !== 'undefined' && 'speechSynthesis' in window,
  )

  useEffect(() => {
    return () => {
      try {
        recognitionRef.current?.abort?.()
      } catch {
        recognitionRef.current?.stop?.()
      }

      recognitionRef.current = null

      if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
        window.speechSynthesis.cancel()
      }
    }
  }, [])

  const stopSpeaking = () => {
    if (typeof window === 'undefined' || !('speechSynthesis' in window)) return

    window.speechSynthesis.cancel()
    setSpeakingMessageId('')
  }

  const speakMessage = (messageId, text) => {
    if (typeof window === 'undefined' || !('speechSynthesis' in window)) {
      return { ok: false, reason: 'Tu navegador no soporta reproducción por voz.' }
    }

    if (!text?.trim()) {
      return { ok: false, reason: 'El mensaje no tiene contenido para reproducir.' }
    }

    if (speakingMessageId === messageId) {
      window.speechSynthesis.cancel()
      setSpeakingMessageId('')
      return { ok: true, toggledOff: true }
    }

    window.speechSynthesis.cancel()

    const utterance = new SpeechSynthesisUtterance(text)
    const voices = window.speechSynthesis.getVoices()
    const selectedVoice = pickVoice(voices)

    utterance.lang = selectedVoice?.lang || 'es-GT'
    utterance.voice = selectedVoice
    utterance.rate = 1
    utterance.pitch = 1
    utterance.onstart = () => setSpeakingMessageId(messageId)
    utterance.onend = () => setSpeakingMessageId('')
    utterance.onerror = () => setSpeakingMessageId('')

    window.speechSynthesis.speak(utterance)

    return { ok: true, toggledOff: false }
  }

  const startListening = async ({ onTranscript, onError }) => {
    const { recognition, SpeechRecognitionCtor } = createRecognitionInstance()

    if (!recognition) {
      onError?.('Tu navegador no soporta reconocimiento de voz.', 'unsupported')
      return { ok: false, mode: 'unsupported' }
    }

    const onDeviceReady = await ensureOnDeviceRecognition(SpeechRecognitionCtor, recognition)
    if (!onDeviceReady.ok) {
      onError?.(onDeviceReady.reason, 'local-unavailable')
      return { ok: false, mode: 'fallback', reason: onDeviceReady.reason }
    }

    recognition.onresult = (event) => {
      const transcript = Array.from(event.results)
        .map((result) => result[0]?.transcript || '')
        .join(' ')
        .trim()

      onTranscript?.(transcript)
    }

    recognition.onerror = (event) => {
      setIsListening(false)
      onError?.(mapRecognitionError(event.error), event.error)
    }

    recognition.onend = () => {
      setIsListening(false)
      recognitionRef.current = null
    }

    recognitionRef.current = recognition

    try {
      setIsListening(true)
      recognition.start()
      return { ok: true, mode: 'local' }
    } catch (error) {
      recognitionRef.current = null
      setIsListening(false)
      const message =
        error instanceof Error
          ? `No se pudo iniciar el dictado. ${error.message}`
          : 'No se pudo iniciar el dictado en este navegador.'
      onError?.(message, 'start-failed')
      return { ok: false, mode: 'fallback', reason: message }
    }
  }

  const stopListening = () => {
    try {
      recognitionRef.current?.stop?.()
    } catch {
      recognitionRef.current?.abort?.()
    }

    recognitionRef.current = null
    setIsListening(false)
  }

  return {
    isListening,
    speakingMessageId,
    isSpeechRecognitionSupported,
    isSpeechSynthesisSupported,
    speakMessage,
    stopSpeaking,
    startListening,
    stopListening,
  }
}
