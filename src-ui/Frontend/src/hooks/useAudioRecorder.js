import { useEffect, useRef, useState } from 'react'

function mergeFloat32Chunks(chunks) {
  const totalLength = chunks.reduce((sum, chunk) => sum + chunk.length, 0)
  const merged = new Float32Array(totalLength)
  let offset = 0

  chunks.forEach((chunk) => {
    merged.set(chunk, offset)
    offset += chunk.length
  })

  return merged
}

function downsampleBuffer(buffer, inputSampleRate, targetSampleRate) {
  if (inputSampleRate === targetSampleRate) {
    return buffer
  }

  const sampleRateRatio = inputSampleRate / targetSampleRate
  const newLength = Math.round(buffer.length / sampleRateRatio)
  const result = new Float32Array(newLength)
  let offsetResult = 0
  let offsetBuffer = 0

  while (offsetResult < result.length) {
    const nextOffsetBuffer = Math.round((offsetResult + 1) * sampleRateRatio)
    let accum = 0
    let count = 0

    for (let index = offsetBuffer; index < nextOffsetBuffer && index < buffer.length; index += 1) {
      accum += buffer[index]
      count += 1
    }

    result[offsetResult] = count > 0 ? accum / count : 0
    offsetResult += 1
    offsetBuffer = nextOffsetBuffer
  }

  return result
}

function encodeWav(samples, sampleRate) {
  const bytesPerSample = 2
  const blockAlign = bytesPerSample
  const buffer = new ArrayBuffer(44 + samples.length * bytesPerSample)
  const view = new DataView(buffer)

  const writeString = (offset, value) => {
    for (let index = 0; index < value.length; index += 1) {
      view.setUint8(offset + index, value.charCodeAt(index))
    }
  }

  writeString(0, 'RIFF')
  view.setUint32(4, 36 + samples.length * bytesPerSample, true)
  writeString(8, 'WAVE')
  writeString(12, 'fmt ')
  view.setUint32(16, 16, true)
  view.setUint16(20, 1, true)
  view.setUint16(22, 1, true)
  view.setUint32(24, sampleRate, true)
  view.setUint32(28, sampleRate * blockAlign, true)
  view.setUint16(32, blockAlign, true)
  view.setUint16(34, 16, true)
  writeString(36, 'data')
  view.setUint32(40, samples.length * bytesPerSample, true)

  let offset = 44
  samples.forEach((sample) => {
    const normalized = Math.max(-1, Math.min(1, sample))
    view.setInt16(offset, normalized < 0 ? normalized * 0x8000 : normalized * 0x7fff, true)
    offset += 2
  })

  return new Blob([buffer], { type: 'audio/wav' })
}

export function useAudioRecorder() {
  const audioContextRef = useRef(null)
  const mediaStreamRef = useRef(null)
  const sourceNodeRef = useRef(null)
  const processorNodeRef = useRef(null)
  const audioChunksRef = useRef([])
  const recordingOptionsRef = useRef({})
  const recordingStartedAtRef = useRef(0)
  const silenceStartedAtRef = useRef(null)
  const stopInProgressRef = useRef(false)
  const [isRecording, setIsRecording] = useState(false)
  const [isRecordingSupported] = useState(
    () => typeof navigator !== 'undefined' && Boolean(navigator.mediaDevices?.getUserMedia),
  )

  useEffect(() => {
    return () => {
      try {
        processorNodeRef.current?.disconnect()
        sourceNodeRef.current?.disconnect()
      } catch {
        // noop
      }

      mediaStreamRef.current?.getTracks()?.forEach((track) => track.stop())
      audioContextRef.current?.close?.()
    }
  }, [])

  const finalizeRecording = async () => {
    if (stopInProgressRef.current) {
      return null
    }

    stopInProgressRef.current = true

    try {
      processorNodeRef.current?.disconnect()
      sourceNodeRef.current?.disconnect()
      mediaStreamRef.current?.getTracks()?.forEach((track) => track.stop())

      const audioContext = audioContextRef.current
      if (!audioContext) {
        return null
      }

      const merged = mergeFloat32Chunks(audioChunksRef.current)
      const resampled = downsampleBuffer(merged, audioContext.sampleRate, 16000)
      const wavBlob = encodeWav(resampled, 16000)

      await audioContext.close()

      audioContextRef.current = null
      mediaStreamRef.current = null
      sourceNodeRef.current = null
      processorNodeRef.current = null
      audioChunksRef.current = []
      recordingOptionsRef.current = {}
      recordingStartedAtRef.current = 0
      silenceStartedAtRef.current = null
      setIsRecording(false)

      return wavBlob
    } finally {
      stopInProgressRef.current = false
    }
  }

  const startRecording = async (options = {}) => {
    if (!isRecordingSupported) {
      throw new Error('Tu navegador no soporta grabación de audio local.')
    }

    if (isRecording || stopInProgressRef.current) {
      return
    }

    const stream = await navigator.mediaDevices.getUserMedia({
      audio: {
        channelCount: 1,
        noiseSuppression: true,
        echoCancellation: true,
      },
    })

    const AudioContextCtor = window.AudioContext || window.webkitAudioContext
    const audioContext = new AudioContextCtor()
    const sourceNode = audioContext.createMediaStreamSource(stream)
    const processorNode = audioContext.createScriptProcessor(4096, 1, 1)
    const {
      autoStop = false,
      silenceThreshold = 0.015,
      silenceDurationMs = 1500,
      minRecordingMs = 1200,
      onAutoStop,
    } = options

    audioChunksRef.current = []
    recordingOptionsRef.current = {
      autoStop,
      silenceThreshold,
      silenceDurationMs,
      minRecordingMs,
      onAutoStop,
    }
    recordingStartedAtRef.current = Date.now()
    silenceStartedAtRef.current = null

    processorNode.onaudioprocess = (event) => {
      const inputData = event.inputBuffer.getChannelData(0)
      audioChunksRef.current.push(new Float32Array(inputData))

      if (!recordingOptionsRef.current.autoStop || stopInProgressRef.current) {
        return
      }

      let sumSquares = 0
      for (let index = 0; index < inputData.length; index += 1) {
        sumSquares += inputData[index] * inputData[index]
      }

      const rms = Math.sqrt(sumSquares / inputData.length)
      const now = Date.now()

      if (rms > recordingOptionsRef.current.silenceThreshold) {
        silenceStartedAtRef.current = null
        return
      }

      if (!silenceStartedAtRef.current) {
        silenceStartedAtRef.current = now
        return
      }

      const recordingElapsed = now - recordingStartedAtRef.current
      const silenceElapsed = now - silenceStartedAtRef.current

      if (
        recordingElapsed >= recordingOptionsRef.current.minRecordingMs &&
        silenceElapsed >= recordingOptionsRef.current.silenceDurationMs
      ) {
        const onAutoStopCallback = recordingOptionsRef.current.onAutoStop
        Promise.resolve()
          .then(() => finalizeRecording())
          .then((audioBlob) => {
            if (audioBlob) {
              onAutoStopCallback?.(audioBlob)
            }
          })
          .catch(() => {
            // noop
          })
      }
    }

    sourceNode.connect(processorNode)
    processorNode.connect(audioContext.destination)

    audioContextRef.current = audioContext
    mediaStreamRef.current = stream
    sourceNodeRef.current = sourceNode
    processorNodeRef.current = processorNode
    setIsRecording(true)
  }

  const stopRecording = async () => {
    if (!isRecording) {
      return null
    }
    return finalizeRecording()
  }

  const cancelRecording = async () => {
    if (!isRecording) return

    processorNodeRef.current?.disconnect()
    sourceNodeRef.current?.disconnect()
    mediaStreamRef.current?.getTracks()?.forEach((track) => track.stop())
    await audioContextRef.current?.close?.()

    audioContextRef.current = null
    mediaStreamRef.current = null
    sourceNodeRef.current = null
    processorNodeRef.current = null
    audioChunksRef.current = []
    recordingOptionsRef.current = {}
    recordingStartedAtRef.current = 0
    silenceStartedAtRef.current = null
    setIsRecording(false)
  }

  return {
    isRecording,
    isRecordingSupported,
    startRecording,
    stopRecording,
    cancelRecording,
  }
}
