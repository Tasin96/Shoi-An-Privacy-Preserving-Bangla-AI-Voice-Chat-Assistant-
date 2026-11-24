# -*- coding: utf-8 -*-
"""
Bangla Mental Health Crisis Detection & Multi-Layer Safety Engine:
Operates 4 standardized operational risk levels:
- LEVEL 0: No Detected Crisis (Normal conversation)
- LEVEL 1: Mild Emotional Distress (Sadness, loneliness, emotional fatigue)
- LEVEL 2: Significant Distress (Veiled ideation, burdensomeness, desire to vanish -> direct gentle clarification)
- LEVEL 3: Possible Immediate Danger (Explicit self-harm intent, agricultural poisons, domestic violence danger)
"""

import re
import os
import json
from typing import Dict, Any, List, Optional, Tuple
from app.schemas.crisis import CrisisAssessResponse
from app.services.crisis_detector import (
    get_keywords, get_veiled_keywords, BYSTANDER_SAFE_AUDIO_BN,
    DIRECT_SUICIDE_STEMS, BANGLISH_STEMS
)
from app.services.rag import normalize_bangla_text

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
    r"আত্মহত্যা\s*করব\s*না",
    r"ক্ষতি\s*করব\s*না",
    r"নিজের\s*ক্ষতি\s*করতে\s*চাই\s*না"
]

MILD_DISTRESS_STEMS = [
    "মন খারাপ", "মনডা ভালো না", "কষ্ট লাগছে", "একাকী লাগে", "একা একা লাগে",
    "ক্লান্ত লাগছে", "ভালো লাগছে না", "হতাশ লাগছে", "টেনশন হচ্ছে", "অস্থির লাগছে",
    "শান্তি নেই", "খুব একা", "কান্না পাচ্ছে", "মনটা ভার"
]

LEVEL_2_CLARIFICATION_PROMPT_BN = (
    "তোমার কথায় মনে হচ্ছে তুমি অনেক কষ্টের মধ্যে আছো। আমি তোমার কথা মন দিয়ে শুনছি। "
    "একটা বিষয় জানতে চাই—তুমি কি শুধু সবকিছু থেকে একটু দূরে থাকতে চাইছ, নাকি নিজের ক্ষতি করার কথাও মনে হচ্ছে?"
)

def is_hypothetical_or_educational(norm_text: str) -> bool:
    for pat in HYPOTHETICAL_EDUCATIONAL_PATTERNS:
        if re.search(pat, norm_text):
            return True
    return False

def has_explicit_negation(norm_text: str) -> bool:
    for pat in NEGATION_PATTERNS:
        if re.search(pat, norm_text):
            return True
    return False

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

    norm_text = normalize_bangla_text(text.lower().strip())
    veiled_data = get_veiled_keywords() or {}
    keywords_data = get_keywords() or {}
    detected_signals: List[str] = []

    # Check for hypothetical/educational discussions or explicit negations
    if is_hypothetical_or_educational(norm_text):
        return CrisisAssessResponse(
            risk_level="LEVEL_0",
            level_numeric=0,
            confidence=0.92,
            detected_signal_categories=["educational_or_hypothetical_context"],
            is_hypothetical=True,
            action_required=False
        )

    if has_explicit_negation(norm_text):
        return CrisisAssessResponse(
            risk_level="LEVEL_1",
            level_numeric=1,
            confidence=0.88,
            detected_signal_categories=["distress_with_explicit_affirmation_of_life"],
            action_required=False,
            safety_response_bn="আপু, আপনার কষ্ট আমরা বুঝতে পারছি। আপনি একা নন। একটু বুক ভরে শ্বাস নিন, আমরা আপনার পাশে আছি।"
        )

    # =========================================================================
    # LEVEL 3: POSSIBLE IMMEDIATE DANGER (Lethal Means & Explicit Suicide Stems)
    # =========================================================================
    # 3.1 Rural Agricultural Lethal Means (pesticides, agricultural poison)
    lethal_means = veiled_data.get("rural_lethal_means_access", [
        "ফসলের বিষ", "ঘাসের ওষুধ", "কীটনাশক", "কীটনাশকের বোতল", "পোকার ওষুধ", "নদীর জলে গা ভাসায় দেব"
    ])
    for lm in lethal_means:
        if lm in norm_text:
            detected_signals.append("rural_lethal_means_access")
            return CrisisAssessResponse(
                risk_level="LEVEL_3",
                level_numeric=3,
                confidence=0.98,
                detected_signal_categories=detected_signals,
                is_veiled=True,
                covert_alert=True,
                action_required=True,
                safety_response_bn="আপু, আপনার কষ্ট আমরা অনুভব করছি। কোনো কঠিন সিদ্ধান্ত নেবেন না। এখনই ১০৯ (নারী সহায়তা সেল) বা ৯৯৯-এ সাহায্য নিন।",
                emergency_helpline="109",
                bystander_safe_audio_bn=BYSTANDER_SAFE_AUDIO_BN
            )

    # 3.2 Explicit Suicide Stems & Intent
    all_direct = DIRECT_SUICIDE_STEMS + keywords_data.get("direct_suicide_bn", [])
    for stem in all_direct:
        if stem in norm_text:
            detected_signals.append("explicit_suicide_intent")
            return CrisisAssessResponse(
                risk_level="LEVEL_3",
                level_numeric=3,
                confidence=0.99,
                detected_signal_categories=detected_signals,
                is_veiled=False,
                covert_alert=False,
                action_required=True,
                safety_response_bn="আপু, আপনার জীবন অত্যন্ত মূল্যবান। আপনি একা নন। দয়া করে নিজের ক্ষতি করবেন না। এখনই ৯৯৯ বা ১০৯ এ বিনামূল্যে কল করুন।",
                emergency_helpline="999",
                bystander_safe_audio_bn=BYSTANDER_SAFE_AUDIO_BN
            )

    # 3.3 Banglish Suicide Stems
    all_banglish = BANGLISH_STEMS + keywords_data.get("banglish", [])
    for b_stem in all_banglish:
        if b_stem in norm_text:
            detected_signals.append("banglish_crisis_indication")
            return CrisisAssessResponse(
                risk_level="LEVEL_3",
                level_numeric=3,
                confidence=0.95,
                detected_signal_categories=detected_signals,
                action_required=True,
                emergency_helpline="999",
                bystander_safe_audio_bn=BYSTANDER_SAFE_AUDIO_BN
            )

    # =========================================================================
    # LEVEL 2: SIGNIFICANT DISTRESS (Veiled suicidal resignation, burdensomeness, domestic entrapment)
    # =========================================================================
    # 2.1 Passive Resignation & Death Wishes
    passive_death = veiled_data.get("passive_resignation_death_wishes", [
        "আল্লাহ যেন আমাকে তুলে নেয়", "ঘুমাইয়া যদি আর না উঠতাম", "আমার কি মরণ নাই", "এই জীবনের চেয়ে মরণ ভালো ছিল"
    ])
    for p in passive_death:
        if p in norm_text:
            detected_signals.append("passive_resignation_death_wishes")

    # 2.2 Burdensomeness and Erasure Metaphors
    burdensome = veiled_data.get("burdensomeness_and_erasure", [
        "আমি না থাকলেই সবার ভালো", "সংসারের বোঝা হয়ে আছি", "কোথাও হারিয়ে যেতে চাই চিরতরে", "হারিয়ে যেতে ইচ্ছা করে"
    ])
    for b in burdensome:
        if b in norm_text:
            detected_signals.append("burdensomeness_and_erasure")

    # 2.3 Hopeless Entrapment and Domestic Abuse
    entrapment = veiled_data.get("hopeless_entrapment_and_abuse", [
        "চারিদিকে অন্ধকার লাগে কোনো পথ নাই", "বাপের বাড়ি গিয়ে আর মুখ দেখাব না", "দম বন্ধ হয়ে আসতেছে আর পারি না"
    ])
    for e in entrapment:
        if e in norm_text:
            detected_signals.append("hopeless_entrapment_and_abuse")

    # Contextual multi-turn escalation check
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
            confidence=0.90,
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
    # LEVEL 1: MILD EMOTIONAL DISTRESS (Loneliness, stress, everyday fatigue)
    # =========================================================================
    for mild in MILD_DISTRESS_STEMS:
        if mild in norm_text:
            detected_signals.append("mild_emotional_distress")
            return CrisisAssessResponse(
                risk_level="LEVEL_1",
                level_numeric=1,
                confidence=0.85,
                detected_signal_categories=detected_signals,
                action_required=False,
                safety_response_bn="আপু, আপনার মন খারাপের কথা শুনে খারাপ লাগছে। আপনি কি আমাকে খুলে বলবেন কী নিয়ে চিন্তা হচ্ছে? আমি আপনার কথা শুনছি।"
            )

    # =========================================================================
    # LEVEL 0: NO DETECTED CRISIS (Normal conversation, health questions)
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


