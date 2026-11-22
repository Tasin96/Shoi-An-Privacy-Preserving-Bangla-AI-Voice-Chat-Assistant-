from fastapi import APIRouter, Request, UploadFile, File, Form, HTTPException, status
from typing import Optional
import uuid
from app.schemas.chat import VoiceResponse
from app.services.asr import transcribe_audio
from app.services.llm import llm_service
from app.services.tts import text_to_speech_base64
from app.services.session_memory import session_memory

router = APIRouter(prefix="/voice", tags=["Voice First Pipeline"])

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

    # Synthesize Bangla speech reply
    audio_b64 = await text_to_speech_base64(chat_resp.reply)

    return VoiceResponse(
        transcript=transcript,
        reply_text=chat_resp.reply,
        audio_base64=audio_b64,
        citations=chat_resp.citations or [],
        risk_level=chat_resp.risk_level,
        emergency_payload=chat_resp.emergency_payload,
        session_id=session_id
    )
