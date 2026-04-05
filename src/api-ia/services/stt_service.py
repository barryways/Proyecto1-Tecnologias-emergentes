from __future__ import annotations

import io
import json
import os
import wave
from pathlib import Path

from fastapi import HTTPException, status
from vosk import KaldiRecognizer, Model

BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_MODEL_DIR = BASE_DIR / "data" / "vosk-model-small-es-0.42"
_MODEL_CACHE: Model | None = None


def _get_model_path() -> Path:
    configured_path = os.getenv("STT_MODEL_PATH", "").strip()
    return Path(configured_path).resolve() if configured_path else DEFAULT_MODEL_DIR


def _resolve_model_root(model_path: Path) -> Path:
    required_entries = ("am", "conf", "graph", "ivector")

    if all((model_path / entry).exists() for entry in required_entries):
        return model_path

    nested_candidates = [item for item in model_path.iterdir() if item.is_dir()]
    if len(nested_candidates) == 1:
        nested_path = nested_candidates[0]
        if all((nested_path / entry).exists() for entry in required_entries):
            return nested_path

    return model_path


def _get_model() -> Model:
    global _MODEL_CACHE

    model_path = _get_model_path()
    if not model_path.exists():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "No se encontró el modelo local de voz. Descarga un modelo de Vosk en español "
                f"y colócalo en: {model_path}"
            ),
        )

    model_root = _resolve_model_root(model_path)
    required_entries = ("am", "conf", "graph", "ivector")
    if not all((model_root / entry).exists() for entry in required_entries):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "El modelo local de Vosk no esta completo. "
                f"Descarga y extrae el modelo en: {model_path}"
            ),
        )

    if _MODEL_CACHE is None:
        try:
            _MODEL_CACHE = Model(str(model_root))
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=(
                    "No fue posible cargar el modelo local de voz. "
                    f"Verifica el contenido instalado en: {model_root}"
                ),
            ) from exc

    return _MODEL_CACHE


def _open_wave(audio_bytes: bytes) -> wave.Wave_read:
    try:
        return wave.open(io.BytesIO(audio_bytes), "rb")
    except wave.Error as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El audio recibido no es un WAV PCM valido.",
        ) from exc


def transcribe_wav_audio(audio_bytes: bytes) -> str:
    with _open_wave(audio_bytes) as wav_file:
        if wav_file.getnchannels() != 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El audio debe estar en mono para transcripción local.",
            )

        if wav_file.getsampwidth() != 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El audio debe estar en formato PCM de 16 bits.",
            )

        sample_rate = wav_file.getframerate()
        recognizer = KaldiRecognizer(_get_model(), sample_rate)
        collected_text: list[str] = []

        while True:
            chunk = wav_file.readframes(4000)
            if not chunk:
                break

            if recognizer.AcceptWaveform(chunk):
                result = json.loads(recognizer.Result())
                text = result.get("text", "").strip()
                if text:
                    collected_text.append(text)

        final_result = json.loads(recognizer.FinalResult())
        final_text = final_result.get("text", "").strip()
        if final_text:
            collected_text.append(final_text)

    transcript = " ".join(part for part in collected_text if part).strip()
    if not transcript:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No se pudo obtener texto del audio grabado.",
        )

    return transcript
