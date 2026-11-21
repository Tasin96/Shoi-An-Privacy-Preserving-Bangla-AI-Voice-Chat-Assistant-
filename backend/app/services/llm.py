import os
import httpx
from typing import List, Dict, Any, Optional
from app.config import settings
from app.services.rag import rag_service
from app.services.crisis_detector import detect_crisis
from app.services.chitchat import get_chitchat_response
from app.schemas.chat import ChatMessage, ChatResponse

SYSTEM_PROMPT_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "prompts", "system_bn.md"
)

def get_system_prompt() -> str:
    if os.path.exists(SYSTEM_PROMPT_PATH):
        try:
            with open(SYSTEM_PROMPT_PATH, "r", encoding="utf-8") as f:
                return f.read()
        except Exception:
            pass
    return "You are Shoi, a warm, caring Bangla health assistant for women in rural Bangladesh."

class LLMService:
    def __init__(self):
        self.system_prompt = get_system_prompt()

    async def generate_response(
        self,
        message: str,
        history: Optional[List[ChatMessage]] = None
    ) -> ChatResponse:
        """
        Executes the full pipeline:
        1. Layered safety check (crisis detection)
        2. RAG retrieval over grounded Bangla medical KB
        3. LLM generation (Gemini, OpenAI, or grounded deterministic medical fallback)
        """
        # Step 1: Safety & Crisis Check
        safety_result = detect_crisis(message)
        if safety_result.risk_level == "high":
            return ChatResponse(
                reply=(
                    "আপু, আপনার কষ্ট আমরা বুঝতে পারছি। আপনি একা নন। "
                    "অনুগ্রহ করে নিজের কোনো ক্ষতি করবেন না। এখনই নিচের বাটনে চাপ দিয়ে সাহায্য পাওয়ার ব্যবস্থা করুন।"
                ),
                confidence=1.0,
                risk_level="high",
                emergency_payload=safety_result.emergency_payload
            )

        # Step 1.5: Conversational Chitchat & Greetings Check
        chitchat = get_chitchat_response(message)
        if chitchat:
            reply_text, conf = chitchat
            return ChatResponse(
                reply=reply_text,
                citations=[],
                confidence=conf,
                risk_level="none",
                emergency_payload=None
            )

        # Step 2: RAG Retrieval
        chunks, is_confident = rag_service.retrieve(message, top_k=2)
        citations = [f"{c['title']} ({c['source']})" for c in chunks]

        # If user asks something where we have zero confident medical knowledge
        if not is_confident and len(chunks) == 0:
            return ChatResponse(
                reply=(
                    "আপু, আপনার এই বিষয়টি সম্পর্কে আমার কাছে সুনির্দিষ্ট চিকিৎসা তথ্য নেই। "
                    "ভুল তথ্যের কোনো ঝুঁকি না নিয়ে নিকটস্থ কমিউনিটি ক্লিনিক বা স্বাস্থ্যকর্মীর পরামর্শ নেওয়া সবচেয়ে নিরাপদ হবে।"
                ),
                citations=[],
                confidence=0.3,
                risk_level=safety_result.risk_level
            )

        # Step 3: Call external LLM or Grounded Fallback
        context_text = "\n\n".join([f"[{c['title']} - {c['source']}]:\n{c['text']}" for c in chunks])
        
        reply_text = None
        
        # Try Gemini API if key is present
        if settings.GEMINI_API_KEY:
            try:
                reply_text = await self._call_gemini(message, context_text, history)
            except Exception as e:
                print(f"Gemini API call failed: {e}")
        
        # Try OpenAI API if key is present
        if not reply_text and settings.OPENAI_API_KEY:
            try:
                reply_text = await self._call_openai(message, context_text, history)
            except Exception as e:
                print(f"OpenAI API call failed: {e}")

        # Grounded Medical Response Fallback (Zero-API-key zero-cost high reliability)
        if not reply_text:
            reply_text = self._build_grounded_fallback_reply(message, chunks)

        return ChatResponse(
            reply=reply_text,
            citations=citations,
            confidence=0.9 if is_confident else 0.5,
            risk_level=safety_result.risk_level,
            emergency_payload=safety_result.emergency_payload
        )

    async def _call_gemini(self, message: str, context: str, history: Optional[List[ChatMessage]]) -> Optional[str]:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={settings.GEMINI_API_KEY}"
        
        prompt = (
            f"{self.system_prompt}\n\n"
            f"=== স্বাস্থ্য তথ্য ও নির্দেশনা (Context) ===\n{context}\n\n"
            f"ব্যবহারকারীর প্রশ্ন: {message}\n"
            f"নির্দেশনা: উপরের তথ্য অনুযায়ী সহজ, উষ্ণ বাংলায় অল্প কথায় উত্তর দিন।"
        )
        
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.3, "maxOutputTokens": 300}
        }
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(url, json=payload)
            if resp.status_code == 200:
                data = resp.json()
                return data["candidates"][0]["content"]["parts"][0]["text"].strip()
        return None

    async def _call_openai(self, message: str, context: str, history: Optional[List[ChatMessage]]) -> Optional[str]:
        url = f"{settings.OPENAI_BASE_URL}/chat/completions"
        headers = {"Authorization": f"Bearer {settings.OPENAI_API_KEY}"}
        
        messages = [
            {"role": "system", "content": f"{self.system_prompt}\n\n=== Context ===\n{context}"}
        ]
        if history:
            for h in history[-3:]:
                messages.append({"role": h.role, "content": h.content})
        messages.append({"role": "user", "content": message})
        
        payload = {
            "model": settings.OPENAI_MODEL,
            "messages": messages,
            "temperature": 0.3,
            "max_tokens": 300
        }
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(url, headers=headers, json=payload)
            if resp.status_code == 200:
                data = resp.json()
                return data["choices"][0]["message"]["content"].strip()
        return None

    def _build_grounded_fallback_reply(self, message: str, chunks: List[Dict[str, Any]]) -> str:
        """
        Creates an empathetic, medically precise Bangla response using matched knowledge base chunks.
        """
        top_chunk = chunks[0]
        greeting = "আপু, "
        body = top_chunk["text"]
        closing = f"\n\n(সূত্র: {top_chunk['source']})"
        return f"{greeting}{body}{closing}"

llm_service = LLMService()
