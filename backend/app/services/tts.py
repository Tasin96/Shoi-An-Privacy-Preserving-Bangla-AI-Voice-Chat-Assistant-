import base64
import tempfile
import os
import re
import time
from typing import Optional
from app.config import settings

def normalize_bangla_speech_text(text: str) -> str:
    """
    Normalizes Bangla text for natural, fluent, and correct acoustic pronunciation:
    1. Strips internal markdown, bullets, and parenthetical citations
    2. Transliterates common English acronyms & loanwords to Bangla phonetics (e.g. PCOS -> পিসিওএস)
    3. Converts English numerals (0-9) to Bengali numerals (০-৯) so TTS speaks native Bangla
    4. Expands emergency hotlines (999, 109, 16263) into full phonetic Bangla words
    5. Converts range hyphens (e.g. ১-২ দিন) into natural Bangla phrase (১ থেকে ২ দিন)
    """
    if not text:
        return ""

    # Strip citations
    text = re.sub(r'\([^\)]*সূত্র[^\)]*\)', '', text)
    text = re.sub(r'\[[^\]]*সূত্র[^\]]*\]', '', text)
    text = re.sub(r'\(সূত্র:[^\)]*\)', '', text)
    text = re.sub(r'\[[0-9]+\]', '', text)

    # Phonetic normalization for medical acronyms & common terms
    phonetic_map = [
        (r'\bPCOS\b|\bpcos\b', 'পিসিওএস'),
        (r'\bBMI\b|\bbmi\b', 'বিএমআই'),
        (r'\bEDD\b|\bedd\b', 'ইডিডি'),
        (r'\bLMP\b|\blmp\b', 'এলএমপি'),
        (r'\bAI\b|\bai\b', 'এআই'),
        (r'\bSMS\b|\bsms\b', 'এসএমএস'),
        (r'\bWHO\b|\bwho\b', 'হু'),
        (r'\bDGHS\b|\bdghs\b', 'ডিজিএইচএস'),
        (r'\bDr\b\.?|\bdr\b\.?', 'ডাক্তার'),
        (r'\bmg\b|\bMG\b', 'মিলিগ্রাম'),
        (r'\bkg\b|\bKG\b', 'কেজি'),
        (r'\bml\b|\bML\b', 'মিলি'),
        (r'\bcm\b|\bCM\b', 'সেন্টিমিটার'),
        (r'\bapp\b|\bApp\b', 'অ্যাপ'),
        (r'\bPWA\b|\bpwa\b', 'পিডব্লিউএ'),
        (r'\bUUID\b|\buuid\b', 'ইউআইডি'),
        (r'\bclinic\b|\bClinic\b', 'ক্লিনিক'),
        (r'\bhospital\b|\bHospital\b', 'হাসপাতাল'),
        (r'\bdoctor\b|\bDoctor\b', 'ডাক্তার'),
    ]
    for pattern, replacement in phonetic_map:
        text = re.sub(pattern, replacement, text)

    # Emergency phone numbers expanded phonetically for zero confusion
    text = re.sub(r'\b999\b|\b৯৯৯\b', 'নয় নয় নয়', text)
    text = re.sub(r'\b109\b|\b১০৯\b', 'এক শূন্য নয়', text)
    text = re.sub(r'\b16263\b|\b১৬২৬৩\b', 'এক ছয় দুই ছয় তিন', text)
    text = re.sub(r'\b333\b|\b৩৩৩\b', 'তিন তিন তিন', text)
    text = re.sub(r'\b1098\b|\b১০৯৮\b', 'এক শূন্য নয় আট', text)

    # English digits to Bengali digits
    en_to_bn = {
        '0': '০', '1': '১', '2': '২', '3': '৩', '4': '৪',
        '5': '৫', '6': '৬', '7': '৭', '8': '৮', '9': '৯'
    }
    for en, bn in en_to_bn.items():
        text = text.replace(en, bn)

    # Expand ranges like '১-২ দিন' or '২১-৩৫ দিন' to '১ থেকে ২ দিন'
    text = re.sub(r'([০-৯]+)\s*[-–—]\s*([০-৯]+)', r'\1 থেকে \2', text)

    # Strip markdown symbols and formatting
    text = text.replace('*', '').replace('#', '').replace('`', '').replace('~', '').replace('>', '')
    text = text.replace('[', '').replace(']', '')
    
    # Replace long dashes or colons with natural pause commas
    text = re.sub(r'[-–—:]', ', ', text)
    
    # Normalize multiple punctuation marks
    text = re.sub(r'\.{2,}', '।', text)
    text = re.sub(r'[!]{2,}', '!', text)
    text = re.sub(r'[\?]{2,}', '?', text)
    text = re.sub(r'[,]{2,}', ',', text)
    text = re.sub(r'\s+', ' ', text).strip()

    return text

def smart_speech_truncate(text: str, max_chars: int = 380) -> str:
    """
    Truncates audio speech text at natural sentence boundaries without slicing words.
    """
    if len(text) <= max_chars:
        return text

    cut_zone = text[:max_chars]
    last_danda = max(cut_zone.rfind("।"), cut_zone.rfind("?"), cut_zone.rfind("!"))
    if last_danda >= 200:
        return text[:last_danda + 1].strip()

    last_space = cut_zone.rfind(" ")
    if last_space >= 180:
        return text[:last_space].strip() + "।"

    return cut_zone.strip() + "।"

async def text_to_speech_base64(text: str) -> Optional[str]:
    """
    Converts Bangla text to MP3 audio encoded in base64.
    Uses Microsoft Edge Neural Bangla voice (bn-BD-NabanitaNeural) or gTTS fallback.
    Applies phonetic normalization and prosody smoothing.
    Caches nothing that could identify a user.
    """
    if not text:
        return None

    start_time = time.time()

    # Normalize for acoustic natural speech
    clean_text = normalize_bangla_speech_text(text)
    clean_text = smart_speech_truncate(clean_text, max_chars=380)

    if not clean_text:
        return None

    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_file:
        temp_path = temp_file.name

    try:
        # Method 1: edge-tts (High quality neural voice)
        if settings.TTS_ENGINE == "edge-tts":
            try:
                import edge_tts
                # Paced down slightly (-4%) for warm, soothing rural comprehension
                communicate = edge_tts.Communicate(
                    clean_text,
                    voice=settings.BANGLA_VOICE,
                    rate="-4%",
                    pitch="+0Hz"
                )
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
