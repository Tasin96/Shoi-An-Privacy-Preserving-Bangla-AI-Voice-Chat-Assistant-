import pytest
from app.services.session_memory import SessionMemory, session_memory
from app.services.chitchat import get_chitchat_response, is_medical_query
from app.services.tts import normalize_bangla_speech_text
from app.services.llm import llm_service
from app.schemas.chat import ChatMessage
from fastapi.testclient import TestClient
from app.main import app

def test_session_memory_flow():
    mem = SessionMemory(max_turns=3, ttl_seconds=10)
    sid = "test_sess_01"
    
    assert mem.get_history(sid) == []
    
    mem.add_turn(sid, "আমার তলপেটে ব্যথা", "মাসিকের সময় এমন হতে পারে")
    hist = mem.get_history(sid)
    assert len(hist) == 2
    assert hist[0].role == "user"
    assert hist[0].content == "আমার তলপেটে ব্যথা"
    assert hist[1].role == "assistant"
    assert "মাসিক" in hist[1].content

    # Add multiple turns up to max_turns
    mem.add_turn(sid, "আর কি করব?", "গরম পানির সেঁক নিন")
    mem.add_turn(sid, "কতক্ষণ সেঁক দেব?", "১০ থেকে ১৫ মিনিট")
    mem.add_turn(sid, "ধন্যবাদ সই", "আপনাকেও ধন্যবাদ")
    
    hist = mem.get_history(sid)
    # 3 turns * 2 = 6 messages max
    assert len(hist) == 6
    assert hist[-1].content == "আপনাকেও ধন্যবাদ"

def test_expanded_voice_intents():
    # Cooking / Food
    r1 = get_chitchat_response("আজ কি রান্না করব বলো তো?")
    assert r1 is not None
    assert "ডিম" in r1[0] or "শাক" in r1[0] or "খিচুড়ি" in r1[0] or "ডাল" in r1[0]

    # Sleep / Insomnia
    r2 = get_chitchat_response("আমার রাতে ঘুম আসে না কি করব?")
    assert r2 is not None
    assert "ঘুম" in r2[0] or "পানি" in r2[0] or "শ্বাস" in r2[0]

    # Studies / Exam
    r3 = get_chitchat_response("সামনে পরীক্ষা অনেক ভয় লাগছে")
    assert r3 is not None
    assert "পরীক্ষা" in r3[0] or "পড়াশোনা" in r3[0] or "আস্থা" in r3[0] or "পড়েছ" in r3[0]

    # Anger / Fight
    r4 = get_chitchat_response("আমার খুব রাগ হচ্ছে মেজাজ গরম")
    assert r4 is not None
    assert "পানি" in r4[0] or "রাগ" in r4[0] or "শ্বাস" in r4[0]

    # Baby care
    r5 = get_chitchat_response("বাচ্চা খুব কান্না করছে শান্ত হচ্ছে না")
    assert r5 is not None
    assert "বাচ্চা" in r5[0] or "কোলে" in r5[0]

    # Hair / Skin
    r6 = get_chitchat_response("আমার চুল খুব পড়ছে রূপচর্চার টিপস দাও")
    assert r6 is not None
    assert "চুল" in r6[0] or "তেল" in r6[0] or "পানি" in r6[0]

    # Weakness
    r7 = get_chitchat_response("খুব দুর্বল লাগে মাথা ঘোরে")
    assert r7 is not None
    assert "পানি" in r7[0] or "স্যালাইন" in r7[0] or "দুর্বল" in r7[0] or "মাথা" in r7[0]

    # Prayer / Gratitude
    r8 = get_chitchat_response("আমার জন্য একটু দোয়া করো মন শান্ত হয় যেন")
    assert r8 is not None
    assert "আল্লাহ" in r8[0] or "শান্তি" in r8[0] or "দোয়া" in r8[0] or "প্রার্থনা" in r8[0]

    # Panic / Fast heartbeat
    r9 = get_chitchat_response("আমার বুক ধড়ফড় করছে খুব ভয় লাগছে")
    assert r9 is not None
    assert "ভয়" in r9[0] or "শ্বাস" in r9[0] or "শান্ত" in r9[0]

    # Affection
    r10 = get_chitchat_response("তুমি অনেক মিষ্টি তোমার সাথে কথা বলে ভালো লাগে")
    assert r10 is not None
    assert "আপু" in r10[0]

def test_tts_normalization_and_micropauses():
    text = "আপু শোনো, জরুরি সেবায় ৯৯৯ কল করো। প্রেসার ও diaper চেক করো।"
    norm = normalize_bangla_speech_text(text)
    # Check vocative comma inserted
    assert "আপু," in norm or "শোনো," in norm
    # Check 999 expanded
    assert "নয় নয় নয়" in norm
    assert "ডায়াপার" in norm

@pytest.mark.asyncio
async def test_multi_turn_llm_resolution():
    history = [
        ChatMessage(role="user", content="মাসিকের সময় তীব্র পেটে ব্যথা হয়"),
        ChatMessage(role="assistant", content="এটি ডিসমেনোরিয়া হতে পারে, গরম পানির সেঁক নেওয়া ভালো।")
    ]
    # Follow-up short question
    resp = await llm_service.generate_response(message="আর কি করব?", history=history)
    assert resp is not None
    assert len(resp.reply) > 10

def test_voice_api_with_session():
    client = TestClient(app)
    response = client.post("/voice", json={"direct_transcript": "হ্যালো সই কেমন আছো?"})
    assert response.status_code == 200
    data = response.json()
    assert data["session_id"] is not None
    assert "সই" in data["reply_text"] or "ভালো" in data["reply_text"]
    assert data["audio_base64"] is not None
