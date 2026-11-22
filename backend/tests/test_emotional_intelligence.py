import pytest
from app.services.emotional_intelligence import analyze_female_emotion, build_emotional_comfort_response
from app.services.crisis_detector import detect_crisis
from app.services.llm import llm_service

@pytest.mark.asyncio
async def test_in_laws_family_comfort():
    msg = "আমার শাশুড়ি আমাকে দিনরাত খোঁটা দেয়, সংসারে আমার কোনো শান্তি নেই"
    ctx = analyze_female_emotion(msg)
    assert ctx is not None
    assert ctx["cause_key"] == "IN_LAWS_FAMILY"
    assert "শ্বশুরবাড়ি" in ctx["category_name"]
    resp = await llm_service.generate_response(msg)
    assert "পারুল" in resp.reply
    assert "আত্মসম্মান" in resp.reply

@pytest.mark.asyncio
async def test_infertility_comfort():
    msg = "বিয়ের ৬ বছর পরও বাচ্চা হচ্ছে না বলে সবাই আমাকে অপয়া বলে"
    ctx = analyze_female_emotion(msg)
    assert ctx is not None
    assert ctx["cause_key"] == "INFERTILITY_PREGNANCY"
    resp = await llm_service.generate_response(msg)
    assert "রহিমা" in resp.reply
    assert "অপয়া" in resp.reply

@pytest.mark.asyncio
async def test_pms_hormonal_comfort():
    msg = "মাসিকের আগে কেন আমার এত অকারণ কান্না পায় আর মেজাজ খিটখিটে থাকে?"
    ctx = analyze_female_emotion(msg)
    assert ctx is not None
    assert ctx["cause_key"] == "PMS_HORMONAL"
    resp = await llm_service.generate_response(msg)
    assert "পিএমএস" in resp.reply or "PMS" in resp.reply or "হরমোন" in resp.reply

@pytest.mark.asyncio
async def test_postpartum_depression():
    msg = "বাচ্চা হওয়ার পর আমার ভালো লাগে না, নিজেকে খুব খারাপ মা মনে হয়"
    ctx = analyze_female_emotion(msg)
    assert ctx is not None
    assert ctx["cause_key"] == "POSTPARTUM_DEPRESSION"
    resp = await llm_service.generate_response(msg)
    assert "মোমবাতি" in resp.reply or "মা হওয়া" in resp.reply

@pytest.mark.asyncio
async def test_heartbreak_betrayal():
    msg = "আমার স্বামী পরকীয়া করে আমাকে ধোঁকা দিয়েছে, আমার মন ভেঙে গেছে"
    ctx = analyze_female_emotion(msg)
    assert ctx is not None
    assert ctx["cause_key"] == "HEARTBREAK_BETRAYAL"
    resp = await llm_service.generate_response(msg)
    assert "পদ্মফুল" in resp.reply

@pytest.mark.asyncio
async def test_body_shaming():
    msg = "আমি কালো বলে বারবার বিয়ের সম্বন্ধ ভেঙে যায়, আমার রূপ নেই"
    ctx = analyze_female_emotion(msg)
    assert ctx is not None
    assert ctx["cause_key"] == "BODY_SHAMING"
    resp = await llm_service.generate_response(msg)
    assert "চাঁদ" in resp.reply or "সৌন্দর্য" in resp.reply

@pytest.mark.asyncio
async def test_direct_emergency_call_payload():
    msg = "আমি বিষ খাব আর বেঁচে থাকার ইচ্ছা নেই"
    c_res = detect_crisis(msg)
    assert c_res.risk_level == "high"
    assert c_res.emergency_payload is not None
    assert c_res.emergency_payload.helpline_number == "999"

    resp = await llm_service.generate_response(msg)
    assert resp.risk_level == "high"
    assert "৯৯৯" in resp.reply
    assert resp.emergency_payload is not None
    assert resp.emergency_payload.helpline_number == "999"
    assert resp.emergency_payload.mental_health_helpline == "109"
