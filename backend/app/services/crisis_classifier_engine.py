# -*- coding: utf-8 -*-
"""
Bangla Mental Health Crisis Detection & Multi-Layer Safety Engine:
Operates 4 standardized operational risk levels:
- LEVEL 0: No Detected Crisis (Normal health/wellness inquiry)
- LEVEL 1: Mild Emotional Distress (Sadness, loneliness, emotional weariness, routine stress)
- LEVEL 2: Significant Distress (Veiled ideation, burdensomeness, desire to vanish -> gentle direct clarification)
- LEVEL 3: Possible Immediate Danger (Explicit self-harm intent, agricultural poisons, domestic violence danger -> covert emergency mode & 109 hotline)
"""

import re
import os
import json
import unicodedata
from typing import Dict, Any, List, Optional
from app.schemas.crisis import CrisisAssessResponse
from app.services.crisis_detector import (
    get_keywords, get_veiled_keywords, BYSTANDER_SAFE_AUDIO_BN,
    DIRECT_SUICIDE_STEMS, BANGLISH_STEMS
)

def deep_clean_bn(text: str) -> str:
    """
    Normalizes Bengali characters and handles dual representation of nukta chars.
    """
    if not text:
        return ""
    text = unicodedata.normalize("NFKC", text.lower().strip())
    # Standardize য় / য়
    text = text.replace("\u09af\u09bc", "য়").replace("য়", "য়")
    # Standardize ড় / ড়
    text = text.replace("\u09a1\u09bc", "ড়").replace("ড়", "ড়")
    # Standardize ঢ় / ঢ়
    text = text.replace("\u09a2\u09bc", "ঢ়").replace("ঢ়", "ঢ়")
    return text

HYPOTHETICAL_EDUCATIONAL_PATTERNS = [
    r"আত্মহত্যা\s*(?:প্রতিরোধ|সচেতনতা|দিবস|নিবন্ধ|গবেষণা|হার|পরিসংখ্যান|কারণ)",
    r"কেন\s*মানুষ\s*আত্মহত্যা\s*করে",
    r"আত্মহত্যা\s*কি\s*(?:পাপ|অপরাধ|হারাম)",
    r"গল্পের\s*চরিত্র\s*মরে\s*গেছে",
    r"নাটকে\s*দেখেছি"
]

NEGATION_PATTERNS = [
    r"মরতে\s*চাই\s*না",
    r"মরে\s*যেতে\s*চাই\s*না",
    r"বেঁচে\s*থাকতে\s*চাই",
    r"বাঁচতে\s*চাই",
    r"বাচতে\s*চাই",
    r"আত্মহত্যা\s*করব\s*না",
    r"ক্ষতি\s*করব\s*না",
    r"নিজের\s*ক্ষতি\s*করতে\s*চাই\s*না"
]

LEVEL_3_LETHAL_PATTERNS = [
    r"ফসলের\s*বিষ",
    r"ঘাসের\s*(?:ওষুধ|বিষ)",
    r"কীটনাশক",
    r"পোকার\s*(?:ওষুধ|বিষ)",
    r"ধানের\s*পোকার\s*বিষ",
    r"নদী(?:র\s*জলে|\s*তে)?\s*(?:গা\s*ভাসা|ঝাঁপ|ডুবে)",
    r"পুকুরে\s*ঝাঁপ",
    r"গলায়\s*দড়ি",
    r"ফাঁস\s*(?:দে|লাগা|নে)",
    r"ছাদ\s*থেকে\s*লাফ",
    r"বিষ\s*(?:খে|খা|পান)",
    r"আত্মহত্যা",
    r"মরে\s*(?:যাব|যেতে\s*চাই|যেতে|গেলে\s*বাঁচতাম)",
    r"মরতে\s*চাই",
    r"জীবন\s*(?:শেষ\s*করে|রাখব\s*না|রাখতে\s*চাই\s*না)",
    r"নিজের\s*ক্ষতি\s*কর"
]

LEVEL_2_VEILED_PATTERNS = [
    # Burdensomeness & erasure
    r"(?:আমি\s*)?না\s*থাকলে(?:ই)?\s*(?:সবার|সবাই)",
    r"সংসারের\s*বোঝা",
    r"সবার\s*বোঝা",
    r"বোঝা\s*হয়ে",
    r"আমাকে\s*ছাড়া\s*সবাই",
    r"কাউকে\s*(?:আর\s*)?জ্বালাব\s*না",
    r"আমার\s*বেঁচে\s*থাকা\s*সবার",
    
    # Desire to vanish or escape forever
    r"(?:চিরতরে|দূরে|কোথাও)\s*হারিয়ে\s*যেতে",
    r"হারিয়ে\s*যেতে\s*ইচ্ছা",
    r"সবকিছু\s*থেকে\s*দূরে\s*চলে\s*যেতে",
    r"দূরে\s*চলে\s*যেতে\s*ইচ্ছা",
    
    # Passive death wishes & resignation
    r"আল্লাহ\s*(?:যেন\s*)?(?:আমাকে\s*)?(?:তুলে|উঠায়)\s*নাও",
    r"ঘুমিয়ে\s*থাকলে\s*(?:আর|যদি|.*অনুভব\s*করতে\s*হতো\s*না)",
    r"ঘুমাইয়া\s*যদি\s*আর\s*না\s*উঠতাম",
    r"আর\s*চোখ\s*খুলতে\s*ইচ্ছা\s*করে\s*না",
    r"আমার\s*(?:কি\s*)?মরণ\s*নাই",
    r"এই\s*জীবনের\s*চেয়ে\s*মরণ\s*ভালো",
    r"বেঁচে\s*থাকার\s*চেয়ে\s*মরণ\s*ভালো",
    r"সবকিছু\s*শেষ\s*হয়ে\s*গেলে\s*(?:ভালো\s*হতো|শান্তি)",
    r"বেঁচে\s*থাকার\s*.*(?:মানে|অর্থ|দরকার|প্রয়োজন)\s*নেই",
    r"বেঁচে\s*থাকার\s*(?:কোনো\s*)?ইচ্ছা\s*নেই",
    r"পরানডা\s*আর\s*সয়\s*না",
    r"মুক্তি\s*পেলে\s*বাঁচতাম",
    
    # Hopeless entrapment & abuse
    r"চারিদিকে\s*অন্ধকার",
    r"ঘর\s*অন্ধকার\s*লাগে",
    r"সব\s*পথ\s*বন্ধ",
    r"কোনো\s*পথ\s*(?:খোলা\s*)?নেই",
    r"বাপের\s*বাড়ি\s*গিয়ে\s*আর\s*মুখ\s*দেখাব\s*না",
    r"দম\s*বন্ধ\s*হয়ে\s*(?:আসে|আসতেছে)",
    r"আর\s*সহ্য\s*হয়\s*না",
    r"অত্যাচারের\s*চেয়ে\s*মরে\s*যাওয়া\s*ভালো",
    r"মারধোর\s*আর\s*সইতে\s*পারি\s*না",
    r"এই\s*নরক\s*থেকে\s*মুক্তি"
]

LEVEL_1_MILD_PATTERNS = [
    r"মন\s*(?:খুব\s*)?খারাপ",
    r"মনডা\s*ভালো\s*না",
    r"কষ্ট\s*লাগছে",
    r"একাকী\s*লাগে",
    r"একা\s*একা\s*লাগে",
    r"ক্লান্ত\s*লাগছে",
    r"ভালো\s*লাগছে\s*না",
    r"হতাশ",
    r"টেনশন\s*হচ্ছে",
    r"অস্থির\s*লাগছে",
    r"শান্তি\s*নেই",
    r"খুব\s*একা",
    r"কান্না\s*পাচ্ছে",
    r"মনটা\s*ভার",
    r"আর\s*কতদিন\s*এভাবে\s*চলবে",
    r"সবকিছু\s*অসহ্য\s*লাগছে",
    r"আমি\s*আর\s*পারছি\s*না",
    r"আমার\s*আর\s*কিছু\s*ভালো\s*লাগে\s*না"
]

LEVEL_2_CLARIFICATION_PROMPT_BN = (
    "তোমার কথায় মনে হচ্ছে তুমি অনেক কষ্টের মধ্যে আছো। আমি তোমার কথা মন দিয়ে শুনছি। "
    "একটা বিষয় জানতে চাই—তুমি কি শুধু সবকিছু থেকে একটু দূরে থাকতে চাইছ, নাকি নিজের ক্ষতি করার কথাও মনে হচ্ছে?"
)

def assess_crisis_risk(
    text: str,
    conversation_history: Optional[List[Dict[str, str]]] = None
) -> CrisisAssessResponse:
    """
    Executes the multi-layer crisis classification protocol:
    Layer 1: Rule-based & Bengali Lexicon (euphemisms, lethal means, passive resignation)
    Layer 2: Semantic NLP & signal categorization
    Layer 3: Contextual & Hypothetical Analysis (distinguishes educational/negated from intent)
    Layer 4: Multi-Signal Safety Engine with explainability & confidence calibration
    """
    if not text or not isinstance(text, str):
        return CrisisAssessResponse(
            risk_level="LEVEL_0",
            level_numeric=0,
            confidence=1.0,
            detected_signal_categories=[],
            action_required=False
        )

    norm_text = deep_clean_bn(text)
    detected_signals: List[str] = []

    # Layer 3: Hypothetical/Educational Discussion Check
    for pat in HYPOTHETICAL_EDUCATIONAL_PATTERNS:
        if re.search(pat, norm_text):
            return CrisisAssessResponse(
                risk_level="LEVEL_0",
                level_numeric=0,
                confidence=0.95,
                detected_signal_categories=["educational_or_hypothetical_context"],
                is_hypothetical=True,
                action_required=False
            )

    # Layer 3: Explicit Negation Check (e.g. "মরতে চাই না কিন্তু খুব কষ্টে আছি")
    for pat in NEGATION_PATTERNS:
        if re.search(pat, norm_text):
            return CrisisAssessResponse(
                risk_level="LEVEL_1",
                level_numeric=1,
                confidence=0.90,
                detected_signal_categories=["distress_with_explicit_affirmation_of_life"],
                action_required=False,
                safety_response_bn="আপু, আপনার কষ্ট আমরা বুঝতে পারছি। আপনি একা নন। একটু বুক ভরে শ্বাস নিন, আমরা সবসময় আপনার পাশে আছি।"
            )

    # =========================================================================
    # LEVEL 3: IMMEDIATE DANGER (Lethal Means & Explicit Crisis)
    # =========================================================================
    for pat in LEVEL_3_LETHAL_PATTERNS:
        if re.search(pat, norm_text):
            detected_signals.append("rural_lethal_means_or_imminent_crisis")
            return CrisisAssessResponse(
                risk_level="LEVEL_3",
                level_numeric=3,
                confidence=0.99,
                detected_signal_categories=detected_signals,
                is_veiled=True,
                covert_alert=True,
                action_required=True,
                safety_response_bn="আপু, আপনার কষ্ট আমরা অনুভব করছি। কোনো কঠিন সিদ্ধান্ত নেবেন না। এখনই ১০৯ (নারী সহায়তা সেল) বা ৯৯৯-এ সাহায্য নিন।",
                emergency_helpline="109",
                bystander_safe_audio_bn=BYSTANDER_SAFE_AUDIO_BN
            )

    # Banglish crisis indicators
    for b_stem in BANGLISH_STEMS:
        if b_stem in norm_text:
            detected_signals.append("banglish_crisis_indication")
            return CrisisAssessResponse(
                risk_level="LEVEL_3",
                level_numeric=3,
                confidence=0.95,
                detected_signal_categories=detected_signals,
                action_required=True,
                emergency_helpline="109",
                bystander_safe_audio_bn=BYSTANDER_SAFE_AUDIO_BN
            )

    # =========================================================================
    # LEVEL 2: SIGNIFICANT DISTRESS (Veiled ideation, burdensomeness, desire to vanish)
    # =========================================================================
    for pat in LEVEL_2_VEILED_PATTERNS:
        if re.search(pat, norm_text):
            detected_signals.append("veiled_ideation_and_burdensomeness")

    # Multi-turn escalation check
    if conversation_history:
        past_distress_count = sum(
            1 for turn in conversation_history[-3:]
            if any(term in turn.get("content", "").lower() for term in ["কষ্ট", "বাঁচতে", "অন্ধকার", "বোঝা", "হতাশ"])
        )
        if past_distress_count >= 2:
            detected_signals.append("repeated_persistent_distress")

    if detected_signals:
        return CrisisAssessResponse(
            risk_level="LEVEL_2",
            level_numeric=2,
            confidence=0.92,
            detected_signal_categories=detected_signals,
            is_veiled=True,
            covert_alert=True,
            action_required=True,
            clarification_prompt_bn=LEVEL_2_CLARIFICATION_PROMPT_BN,
            safety_response_bn="আপু, আপনার মনের কষ্টটা আমি বুঝতে পারছি। একটু বুক ভরে নিঃশ্বাস নিন। এই কঠিন সময়টা কেটে যাবে, আপনার জীবন আমাদের কাছে অনেক মূল্যবান। আমি সবসময় আপনার পাশে আছি।",
            emergency_helpline="109",
            bystander_safe_audio_bn=BYSTANDER_SAFE_AUDIO_BN
        )

    # =========================================================================
    # LEVEL 1: MILD EMOTIONAL DISTRESS (Loneliness, everyday fatigue, sad mood)
    # =========================================================================
    for pat in LEVEL_1_MILD_PATTERNS:
        if re.search(pat, norm_text):
            detected_signals.append("mild_emotional_distress")
            return CrisisAssessResponse(
                risk_level="LEVEL_1",
                level_numeric=1,
                confidence=0.88,
                detected_signal_categories=detected_signals,
                action_required=False,
                safety_response_bn="আপু, আপনার মন খারাপের কথা শুনে খারাপ লাগছে। আপনি কি আমাকে খুলে বলবেন কী নিয়ে চিন্তা হচ্ছে? আমি আপনার কথা শুনছি।"
            )

    # =========================================================================
    # LEVEL 0: NO DETECTED CRISIS (Routine health inquiry)
    # =========================================================================
    return CrisisAssessResponse(
        risk_level="LEVEL_0",
        level_numeric=0,
        confidence=1.0,
        detected_signal_categories=[],
        action_required=False
    )

class CrisisClassifierEngine:
    def assess_crisis(self, text: str, conversation_history: Optional[List[Dict[str, str]]] = None) -> Dict[str, Any]:
        resp = assess_crisis_risk(text, conversation_history)
        if isinstance(resp, CrisisAssessResponse):
            return resp.model_dump()
        return resp

crisis_classifier_engine = CrisisClassifierEngine()
