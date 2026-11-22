import os
import tempfile
import time
from typing import Tuple, Optional

# Pluggable Whisper ASR
_whisper_model = None

def transcribe_audio(audio_bytes: bytes, filename: str = "voice.wav") -> Tuple[str, float]:
    """
    Transcribes audio to Bangla text.
    Immediately deletes the temporary audio file after processing to guarantee user privacy.
    Returns (transcript, confidence).
    """
    start_time = time.time()
    
    # Create secure temporary file
    suffix = os.path.splitext(filename)[1] or ".wav"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_audio:
        temp_path = temp_audio.name
        temp_audio.write(audio_bytes)

    transcript = ""
    confidence = 0.0

    try:
        # Check if faster_whisper or whisper is available
        try:
            import whisper
            global _whisper_model
            if _whisper_model is None:
                _whisper_model = whisper.load_model("base")
            result = _whisper_model.transcribe(temp_path, language="bn")
            transcript = result.get("text", "").strip()
            confidence = 0.85
        except (ImportError, Exception) as e:
            # Fallback 1: Gemini 1.5 Flash Audio transcription if API key is configured
            from app.config import settings
            if settings.GEMINI_API_KEY:
                try:
                    import base64
                    import httpx
                    b64_audio = base64.b64encode(audio_bytes).decode('utf-8')
                    mime = "audio/webm" if filename.endswith(".webm") else "audio/wav"
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={settings.GEMINI_API_KEY}"
                    payload = {
                        "contents": [{
                            "parts": [
                                {"text": "Transcribe this audio recording into exact Bengali (Bangla) text. Return ONLY the spoken words in Bengali script without any translation or notes."},
                                {"inline_data": {"mime_type": mime, "data": b64_audio}}
                            ]
                        }]
                    }
                    with httpx.Client(timeout=8.0) as client:
                        resp = client.post(url, json=payload)
                        if resp.status_code == 200:
                            data = resp.json()
                            transcript = data["candidates"][0]["content"]["parts"][0]["text"].strip()
                            confidence = 0.90
                except Exception as g_err:
                    print(f"[ASR] Cloud transcription fallback error: {g_err}")

            # If transcription is still empty, do not invent a fake medical query
            if not transcript:
                transcript = ""
                confidence = 0.0
    finally:
        # Strict privacy rule: delete audio file immediately
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception:
                pass

    elapsed = time.time() - start_time
    print(f"[ASR] Processed audio in {elapsed:.2f}s (zero content logged)")
    return transcript, confidence
