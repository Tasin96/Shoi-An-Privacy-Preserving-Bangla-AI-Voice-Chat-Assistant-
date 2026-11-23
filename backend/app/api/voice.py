from fastapi import APIRouter, Request, UploadFile, File, Form, HTTPException, status
from typing import Optional
import uuid
from app.schemas.chat import VoiceResponse
from app.services.asr import transcribe_audio
from app.services.llm import llm_service
from app.services.tts import text_to_speech_base64
from app.services.session_memory import session_memory

router = APIRouter(prefix="/voice", tags=["Voice First Pipeline"])

def generate_voice_suggestions(topic: Optional[str], text: str) -> list[str]:
    if not topic:
        return [
            "🌸 কেমন আছো সই?",
            "🩸 পিরিয়ডের ব্যথা কমানোর উপায়",
            "🤰 গর্ভকালীন যত্ন কেমন হবে?"
        ]
    if topic == "abdominal_pain":
        return [
            "বাইরের অস্বাস্থ্যকর খাবার খেয়েছেন কি?",
            "গ্যাস বা এসিডিটির সমস্যা আছে কি?",
            "ব্যথাটা পেটের ঠিক কোন অংশে হচ্ছে?"
        ]
    elif topic == "menstrual_basics":
        return [
            "স্বাভাবিক মাসিক চক্র কতদিনের?",
            "মাসিকে কেমন যত্ন নেওয়া উচিত?",
            "প্যাড ব্যবহারের সঠিক নিয়ম"
        ]
    elif topic == "menstrual_pain":
        return [
            "গরম পানির সেঁক কীভাবে নেব?",
            "মাসিকে কী কী খাবার খাওয়া ভালো?",
            "কখন ডাক্তারের কাছে যাওয়া দরকার?"
        ]
    elif topic == "pcos":
        return [
            "পিসিওএস এর প্রাথমিক লক্ষণ কি?",
            "ওজন কমানোর সহজ উপায় কি?",
            "মাসিক নিয়মিত করার উপায় বলো"
        ]
    elif topic == "pregnancy":
        return [
            "গর্ভকালীন ৫টি প্রধান বিপদচিহ্ন কি?",
            "বাচ্চার নড়াচড়া কখন বোঝা যায়?",
            "গর্ভবতী মায়ের পুষ্টিকর খাদ্যতালিকা"
        ]
    elif topic == "emotional_distress":
        return [
            "মন ভালো করার গল্প শোনাও",
            "একটু সান্ত্বনা দাও",
            "আমার মন খুব ভার লাগছে"
        ]
    elif topic == "hygiene_uti":
        return [
            "সাদা স্রাব হলে কী করণীয়?",
            "প্রস্রাবে জ্বালাপোড়া কমানোর ঘরোয়া উপায়",
            "প্যাড ব্যবহারের সঠিক নিয়ম"
        ]
    elif topic == "cooking_nutrition":
        return [
            "সহজ পুষ্টিকর রান্নার উপায় বলো",
            "রক্ত বাড়াতে কী খাওয়া উচিত?",
            "ডিম ও শাকের সহজ রেসিপি"
        ]
    elif topic == "sleep_insomnia":
        return [
            "ঘুমের আগে কী করলে ভালো ঘুম হয়?",
            "অনিদ্রা দূর করার উপায়",
            "মাথা ঠান্ডা রাখার টিপস"
        ]
    elif topic == "baby_care":
        return [
            "বাচ্চা কান্না করলে কীভাবে শান্ত করব?",
            "বাচ্চার পেটে গ্যাস হলে কী করণীয়?",
            "শিশুর প্রাথমিক যত্ন"
        ]
    else:
        return [
            "একটু গল্প করো",
            "একটা মজার কথা বলো",
            "শরীর ভালো রাখার টিপস দাও"
        ]

@router.post("", response_model=VoiceResponse)
async def process_voice_message(
    request: Request,
    audio_file: Optional[UploadFile] = File(None),
    direct_transcript: Optional[str] = Form(None)
):
    """
    Voice-first pipeline for low-literacy rural women:
    1. Supports audio file upload (WAV/OGG/M4A/WebM) OR form transcript OR JSON body
    2. ASR transcribes to Bangla (audio destroyed immediately)
    3. Crisis evaluation & RAG retrieval
    4. Neural Bangla TTS synthesizes natural audio response
    5. Returns transcript, reply text, and base64 audio for instant playback
    """
    transcript = ""
    session_id = request.headers.get("x-session-id") or ""

    # Check if request is JSON body
    content_type = request.headers.get("content-type", "")
    if "application/json" in content_type:
        try:
            body = await request.json()
            transcript = body.get("direct_transcript") or body.get("message") or body.get("text") or body.get("query") or ""
            transcript = transcript.strip()
            if not session_id and body.get("session_id"):
                session_id = body.get("session_id")
        except Exception:
            pass

    if not session_id:
        session_id = str(uuid.uuid4())

    if not transcript:
        if audio_file:
            audio_bytes = await audio_file.read()
            if len(audio_bytes) == 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="অডিও ফাইলটি খালি ছিল"
                )
            transcript, _ = transcribe_audio(audio_bytes, audio_file.filename or "recording.wav")
        elif direct_transcript:
            transcript = direct_transcript.strip()

    if not transcript:
        fallback_msg = "দুঃখিত আপু, আপনার কথাটি স্পষ্ট শুনতে পাইনি। দয়া করে আরেকবার বলবেন কি?"
        audio_b64 = await text_to_speech_base64(fallback_msg)
        return VoiceResponse(
            transcript="",
            reply_text=fallback_msg,
            audio_base64=audio_b64,
            citations=[],
            risk_level="none",
            session_id=session_id
        )

    # Multi-turn context memory
    history = session_memory.get_history(session_id)

    # Generate grounded response with multi-turn continuity
    chat_resp = await llm_service.generate_response(message=transcript, history=history)

    # Record turn into ephemeral in-memory session
    session_memory.add_turn(session_id, transcript, chat_resp.reply)
    session_ctx = session_memory.get_session_context(session_id)
    suggestions = generate_voice_suggestions(session_ctx["last_topic"], transcript)

    # Synthesize Bangla speech reply
    audio_b64 = await text_to_speech_base64(chat_resp.reply)

    return VoiceResponse(
        transcript=transcript,
        reply_text=chat_resp.reply,
        audio_base64=audio_b64,
        citations=chat_resp.citations or [],
        risk_level=chat_resp.risk_level,
        emergency_payload=chat_resp.emergency_payload,
        session_id=session_id,
        suggestions=suggestions,
        detected_topic=session_ctx["last_topic"],
        turn_count=session_ctx["turn_count"]
    )
