import json
import os
import re
from typing import Tuple, Dict, Any, Optional
from app.schemas.safety import SafetyCheckResponse, EmergencyPayload

# Path to Bangla crisis keywords
KEYWORDS_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "ml", "crisis", "keywords_bn.json"
)

def get_keywords() -> Dict[str, Any]:
    if os.path.exists(KEYWORDS_PATH):
        try:
            with open(KEYWORDS_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

# Core lexical indicators
DIRECT_SUICIDE_STEMS = [
    "আত্মহত্যা", "মরে যাব", "মরতে চাই", "মরে যেতে চাই", "মরে গেলে", "মরব",
    "ফাঁস দেব", "ফাঁসি", "গলায় দড়ি", "বিষ খাব", "বিষ খেয়ে", "ছাদ থেকে লাফ",
    "জীবন শেষ", "জীবন রাখতে চাই না", "বাঁচতে চাই না", "বাচতে চাই না",
    "বাঁচার ইচ্ছা নেই", "বাচার ইচ্ছা নেই", "বেঁচে থাকার ইচ্ছা নেই",
    "বেঁচে থাকতে চাই না", "বেঁচে থেকে লাভ নেই", "বেচে থেকে লাভ নেই"
]

BANGLISH_STEMS = [
    "morte chai", "morbo", "more jabo", "beche thakte chai na",
    "beche theke lav nai", "jibon sesh", "atmohotta", "suicide",
    "kill myself", "want to die", "end my life", "bish khabo"
]

INDIRECT_DISTRESS_STEMS = [
    "যন্ত্রণা শেষ", "যন্ত্রণা আর সহ্য", "মুক্তি চাই", "কাউকে মুখ দেখানোর",
    "মুখ দেখাতে পারছি না", "ঘৃণা করে", "ঘুমিয়ে পড়তে চাই", "ঘুমাতে চাই চিরতরে",
    "পৃথিবী ছেড়ে", "পরানডা আর সয় না", "বাঁচবার মন চায় না", "মরণ দাও"
]

def detect_crisis(text: str) -> SafetyCheckResponse:
    """
    Multi-layered crisis detector:
    - Layer 1: Deterministic keyword & stem rules (direct suicide, indirect distress, banglish, colloquial)
    - Layer 2: Syntactic urgency & self-harm indicator heuristic
    - High recall prioritized to protect user safety
    - High risk returns emergency payload for user-confirmed 999 calling screen
    - NEVER logs or stores the triggering text
    """
    if not text or not isinstance(text, str):
        return SafetyCheckResponse(risk_level="none", action_required=False)

    normalized_text = text.lower().strip()
    keywords_data = get_keywords()

    # --- Layer 1: Direct Suicide Keywords & Stems (High Risk) ---
    all_direct = DIRECT_SUICIDE_STEMS + keywords_data.get("direct_suicide_bn", [])
    for kw in all_direct:
        if kw in normalized_text:
            return SafetyCheckResponse(
                risk_level="high",
                reason="Direct self-harm indication detected",
                action_required=True,
                emergency_payload=EmergencyPayload(is_emergency=True)
            )

    # Stem combination check for flexible syntax e.g. "বেঁচে থাকার কোনো ইচ্ছা নেই"
    if ("বেঁচে" in normalized_text or "বাঁচ" in normalized_text or "বাচ" in normalized_text) and ("ইচ্ছা নেই" in normalized_text or "লাভ নেই" in normalized_text or "মন চায় না" in normalized_text):
        return SafetyCheckResponse(
            risk_level="high",
            reason="Expressed lack of will to live",
            action_required=True,
            emergency_payload=EmergencyPayload(is_emergency=True)
        )

    if ("বিষ" in normalized_text or "দড়ি" in normalized_text or "ঘুমের ওষুধ" in normalized_text) and ("মরে" in normalized_text or "খাব" in normalized_text or "খেয়ে" in normalized_text or "শেষ" in normalized_text):
        return SafetyCheckResponse(
            risk_level="high",
            reason="Harmful ingestion or lethal intent expression",
            action_required=True,
            emergency_payload=EmergencyPayload(is_emergency=True)
        )

    # Banglish Direct Suicide Check
    all_banglish = BANGLISH_STEMS + keywords_data.get("banglish", [])
    for kw in all_banglish:
        if kw in normalized_text:
            return SafetyCheckResponse(
                risk_level="high",
                reason="Direct self-harm indication detected in romanized text",
                action_required=True,
                emergency_payload=EmergencyPayload(is_emergency=True)
            )

    # --- Layer 2: Indirect Distress & Regional Expressions ---
    all_indirect = INDIRECT_DISTRESS_STEMS + keywords_data.get("indirect_distress_bn", []) + keywords_data.get("regional_colloquial", [])
    for kw in all_indirect:
        if kw in normalized_text:
            return SafetyCheckResponse(
                risk_level="medium",
                reason="Elevated emotional distress or despair detected",
                action_required=True,
                emergency_payload=EmergencyPayload(
                    is_emergency=False,
                    title_bn="আমরা আপনার কথা শুনছি",
                    message_bn="আপনার কষ্ট আমরা উপলব্ধি করছি। অনুগ্রহ করে একজন মানসিক স্বাস্থ্য বিশেষজ্ঞ বা আপনার ভালোবাসার মানুষের সাথে কথা বলুন।"
                )
            )

    return SafetyCheckResponse(risk_level="none", action_required=False)
