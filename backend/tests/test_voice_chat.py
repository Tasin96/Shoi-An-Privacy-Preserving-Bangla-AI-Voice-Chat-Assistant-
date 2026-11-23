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

def test_everyday_conversational_natural_talk():
    # Backchannel & attentive listening
    r1 = get_chitchat_response("হুম")
    assert r1 is not None
    assert "শুনছি" in r1[0] or "বলো" in r1[0]

    r2 = get_chitchat_response("আচ্ছা")
    assert r2 is not None
    assert "আপু" in r2[0]

    # Routine small talk
    r3 = get_chitchat_response("কী করছো এখন?")
    assert r3 is not None
    assert "ফ্রি" in r3[0] or "সময়" in r3[0] or "দিন" in r3[0]

    # Birthday & celebration
    r4 = get_chitchat_response("আজ আমার জন্মদিন")
    assert r4 is not None
    assert "জন্মদিন" in r4[0] or "শুভকামনা" in r4[0]

    # Household chores & body tiredness (not period cramps)
    r5 = get_chitchat_response("আজ অনেক কাজ করেছি শরীর ব্যথা")
    assert r5 is not None
    assert "বিশ্রাম" in r5[0] or "ক্লান্তি" in r5[0] or "খাটুনি" in r5[0] or "পরিশ্রম" in r5[0] or "জিরিয়ে" in r5[0]

    # Gas & Indigestion
    r6 = get_chitchat_response("পেটে গ্যাস হয়েছে পেট ফাঁপা")
    assert r6 is not None
    assert "পানি" in r6[0] or "গ্যাস" in r6[0] or "আরাম" in r6[0]

    # Short voice dismissal
    r7 = get_chitchat_response("না কিছু না")
    assert r7 is not None
    assert "আপু" in r7[0]

    # Fitness & Weight
    r8 = get_chitchat_response("মোটা হয়ে যাচ্ছি ওজন কমাতে চাই")
    assert r8 is not None
    assert "ওজন" in r8[0] or "হাঁটাহাঁটি" in r8[0] or "সুস্থ" in r8[0] or "শরীরের" in r8[0] or "ডায়েট" in r8[0]

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
    assert len(data.get("suggestions", [])) >= 1
    assert data.get("turn_count", 0) >= 1

def test_long_horizon_session_context():
    mem = SessionMemory(max_turns=15, ttl_seconds=86400)
    sid = "long_horizon_user_42"
    
    mem.add_turn(sid, "আমার মাসিকের সময় তলপেট অনেক ব্যথা করে", "গরম পানির সেঁক নিন")
    ctx = mem.get_session_context(sid)
    assert ctx["turn_count"] == 1
    assert ctx["last_topic"] == "menstrual_pain"
    assert "ব্যথা" in ctx["recent_symptoms"]
    assert len(mem.get_history(sid)) == 2

def test_colloquial_dialect_normalization():
    from app.services.rag import normalize_bangla_text
    raw1 = "আমার তলপেট খুব চাবায় আর কামড়ায়"
    norm1 = normalize_bangla_text(raw1)
    assert "ব্যথা" in norm1

    raw2 = "গা মেজমেজ করে আর জর জর লাগে"
    norm2 = normalize_bangla_text(raw2)
    assert "দুর্বলতা" in norm2 or "জ্বর" in norm2
