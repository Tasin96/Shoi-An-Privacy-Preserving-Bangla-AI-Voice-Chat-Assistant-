import base64
import tempfile
import os
import re
import time
from typing import Optional
from app.config import settings

async def text_to_speech_base64(text: str) -> Optional[str]:
    """
    Converts Bangla text to MP3 audio encoded in base64.
    Uses Microsoft Edge Neural Bangla voice (bn-BD-NabanitaNeural) or gTTS fallback.
    Caches nothing that could identify a user.
    """
    if not text:
        return None

    start_time = time.time()
    
    # Clean text of citations and markdown formatting for clearer, faster natural speech
    clean_text = re.sub(r'\([^\)]*সূত্র[^\)]*\)', '', text)
    clean_text = re.sub(r'\[[^\]]*সূত্র[^\]]*\]', '', clean_text)
    clean_text = clean_text.replace("*", "").replace("#", "").replace("[", "").replace("]", "").replace("`", "")
    clean_text = re.sub(r'\s+', ' ', clean_text).strip()
    clean_text = clean_text[:350]  # Keep voice message concise for fast response on mobile network

    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_file:
        temp_path = temp_file.name

    try:
        # Method 1: edge-tts (High quality neural voice)
        if settings.TTS_ENGINE == "edge-tts":
            try:
                import edge_tts
                communicate = edge_tts.Communicate(clean_text, voice=settings.BANGLA_VOICE)
                await communicate.save(temp_path)
            except Exception as e:
                print(f"[TTS] edge-tts error: {e}, attempting gTTS fallback...")
                _fallback_gtts(clean_text, temp_path)
        else:
            _fallback_gtts(clean_text, temp_path)

        if os.path.exists(temp_path) and os.path.getsize(temp_path) > 0:
            with open(temp_path, "rb") as f:
                encoded = base64.b64encode(f.read()).decode("utf-8")
                elapsed = time.time() - start_time
                print(f"[TTS] Synthesized audio in {elapsed:.2f}s (zero content logged)")
                return encoded
    finally:
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception:
                pass

    return None

def _fallback_gtts(text: str, output_path: str):
    try:
        from gtts import gTTS
        tts = gTTS(text=text, lang="bn", slow=False)
        tts.save(output_path)
    except Exception as e:
        print(f"[TTS] gTTS error: {e}")
