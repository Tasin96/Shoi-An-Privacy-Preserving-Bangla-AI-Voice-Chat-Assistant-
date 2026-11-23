# Shoi (সই) — গ্রামীণ নারীদের জন্য কৃত্রিম বুদ্ধিমত্তাভিত্তিক ভয়েস স্বাস্থ্য সহকারী

> **Privacy-preserving Bangla AI voice chat assistant for menstrual health and mental wellness among rural and semi-urban women.**

---

## 🌸 মূল বৈশিষ্ট্যসমূহ (Core Features)

1. **ভয়েস-ফার্স্ট ও সহজ বাংলা (Voice-First & Real-Time Bangla Interaction):**
   - **১৫-টার্ন লং-হরাইজন কন্টেক্সট মেমোরি:** সই পূর্ববর্তী আলোচনা ও উপসর্গের ধারাবাহিকতা মনে রেখে প্রাসঙ্গিক প্রশ্ন ও ফলো-আপ করে (ইন-মেমোরি LRU বাফার, ২৪ ঘণ্টা মেয়াদ, ডিস্কে কোনো PII সংরক্ষিত হয় না)।
   - **আল্ট্রা-ফাস্ট অডিও ক্যাশিং (<০.০০১ সেকেন্ড):** ইন-মেমোরি LRU অডিও ক্যাশের কারণে ঘন ঘন ব্যবহৃত সম্বোধন ও বাক্যের অডিও মুহূর্তের মধ্যে প্লে হয়।
   - **কথোপকথন ইন্টারাপ্ট (Barge-in):** উত্তর চলাকালীন স্ক্রিনে ট্যাপ করলেই তাৎক্ষণিক কণ্ঠ থামিয়ে নতুন কথা শোনার মোডে চলে যায়।
   - **শব্দ ইকুয়ালাইজার ও গতি নিয়ন্ত্রণ:** কথা বলার সময় লাইভ ৪-বার অ্যানিমেটেড ইকুয়ালাইজার এবং ধীরগতির জন্য অডিও স্পিড কন্ট্রোল (১.০x ও ০.৮৫x)।
   - **২৮টি দৈনন্দিন জীবনের কথ্য ইনটেন্ট:** পুষ্টি, সহজ রান্না, অনিদ্রা, পরীক্ষা ও মানসিক ভীতি, ক্লান্তি ও মাথা ঘোরা, শিশুর যত্ন এবং পারিবারিক উদ্বেগের সহানুভূতিশীল আপ্যায়ন।
   - **আঞ্চলিক ভাষার উপসর্গ নরমালাইজেশন:** "পেট কামড়ায়", "গা ম্যাজম্যাজ", "তলপেট চাবায়", "সাদা পানি" ইত্যাদি গ্রামীণ কথ্য অভিব্যক্তি স্বয়ংক্রিয়ভাবে স্ট্যান্ডার্ড চিকিৎসাগত টার্মে রূপান্তর।
   - **ডায়নামিক প্রম্পট চিপস:** স্বল্পসাক্ষর নারীদের সুবিধার্থে প্রতি উত্তরের নিচে স্বয়ংক্রিয় ১-ট্যাপ ফলো-আপ বাটন।

2. **সম্পূর্ণ গোপনীয় ও নিরাপদ (Zero-PII Privacy & OWASP Standards):**
   - কোনো নাম, মোবাইল নম্বর বা ইমেইল সংগ্রহ করা হয় না।
   - সম্পূর্ণ বেনামী র‍্যান্ডম আইডি (Anonymous UUID) দ্বারা পরিচালিত।
   - সার্ভার লগ থেকে স্বয়ংক্রিয়ভাবে আইপি (IP address) ও ফোন নম্বর মুছে দেওয়া হয়।
   - অডিও রূপান্তরের পর তাৎক্ষণিকভাবে মূল অডিও ধ্বংস করা হয়।
   - **"সব তথ্য মুছে ফেলুন" (Wipe All Data):** এক ক্লিকে সার্ভার ও ডিভাইস থেকে চিরতরে সমস্ত তথ্য মুছে ফেলার সুবিধা।

3. **পূর্ণাঙ্গ প্রগ্রেসিভ ওয়েব অ্যাপ (Offline-Ready PWA):**
   - রুট `/manifest.json` এবং `/service-worker.js` এর মাধ্যমে যেকোনো অ্যান্ড্রয়েড ও আইওএস (iOS) ফোনে হোমস্ক্রিন অ্যাপ হিসেবে ইনস্টলযোগ্য।
   - ১৯২px ও ৫১২px হাই-রেজোলিউশন মাস্কেবল অ্যাপ আইকন।
   - দুর্বল নেটওয়ার্কে নির্ভরযোগ্য অফলাইন ক্যাশিং (`shoi-cache-v2`)।

4. **মাসিক ও মেজাজ ট্র্যাকার (Period & Mood Tracker):**
   - মাসিকের চক্রের হিসাব, সম্ভাব্য পরবর্তী তারিখ এবং ওভুলেশন সময়ের পূর্বাভাস (FIGO স্ট্যান্ডার্ড)।
   - ৫টি সহজ ইমোজি দিয়ে প্রতিদিনের মনের অনুভূতি রেকর্ড ও পিএমএস (PMS) বিশ্লেষণ।

5. **পিসিওএস স্বাস্থ্য ঝুঁকি স্ক্রিনিং (PCOS Risk Screening):**
   - ল্যাব টেস্ট ছাড়া সাধারণ লক্ষণ ও অভ্যাসের ভিত্তিতে প্রশিক্ষিত মেশিন লার্নিং মডেল (Random Forest Classifier: 93.7% Accuracy, 0.978 ROC-AUC)।
   - স্ক্রিনিং ফলাফল কখনোই কোনো ডায়াগনোসিস নয়; সবসময় চিকিৎসকের পরামর্শ নেওয়ার দিকনির্দেশনা দেওয়া হয়।

6. **গর্ভকালীন যত্ন ও সময়রেখা (Pregnancy Care & Timeline):**
   - শেষ মাসিকের তারিখ (LMP) থেকে সপ্তাহ ও সম্ভাব্য প্রসব তারিখ (EDD) নির্ণয়।
   - সপ্তাহ অনুযায়ী শিশুর বৃদ্ধি এবং **৫টি মারাত্মক গর্ভকালীন বিপদচিহ্ন** প্রদর্শন।

7. **বহুস্তরী জরুরি মানসিক স্বাস্থ্য সুরক্ষা (Crisis Guardrails & Helplines):**
   - আত্মহত্যা বা চরম হতাশার লক্ষণ ধরা পড়লে সরাসরি শান্ত সমর্থনমূলক স্ক্রিন এবং **৯৯৯ (জাতীয় জরুরি সেবা)**, **১০৯ (নারী ও শিশু নির্যাতন প্রতিরোধ)** এবং **১৬২৬৩ (স্বাস্থ্য বাতায়ন)** এ সহজে কল করার বোতাম।

---

## 🏗️ আর্কিটেকচার ও প্রযুক্তি (Tech Stack)

| স্তর | প্রযুক্তি | বিবরণ |
|---|---|---|
| **Backend API** | FastAPI, Python 3.12 | অতি দ্রুত অ্যাসিনক্রোনাস ব্যাকএন্ড |
| **Frontend** | Responsive Mobile PWA & Flutter | যে কোনো অ্যান্ড্রয়েড ও ব্রাউজারে ইনস্টলযোগ্য |
| **Voice / TTS** | Edge Neural TTS (`bn-BD-NabanitaNeural`) / gTTS | মানুষের মতো স্বাভাবিক বাংলা উচ্চারণ |
| **RAG Engine** | TF-IDF / Semantic Retrieval | WHO ও স্বাস্থ্য অধিদপ্তর (DGHS) নির্দেশিকা দ্বারা নিয়ন্ত্রিত |
| **PCOS ML Model** | Scikit-learn (Random Forest Pipeline) | ৯৩.৭% নির্ভুলতা |
| **Database** | SQLite (Dev) / PostgreSQL (Prod) | সম্পূর্ণ ক্যাসকেডিং ডিলিশন সাপোর্ট |

---

## 🚀 দ্রুত চালু করার নির্দেশিকা (Quick Start Guide)

### ১. ডিপেন্ডেন্সি ইনস্টল ও ভার্চুয়াল এনভায়রনমেন্ট
প্রজেক্টে বিল্ট-ইন পাইথন এনভায়রনমেন্ট প্রস্তুত রয়েছে। ডিপেন্ডেন্সি সক্রিয় করতে:

```powershell
# ভার্চুয়াল এনভায়রনমেন্ট সক্রিয় করুন
.\backend\.venv\Scripts\activate

# অথবা uv দিয়ে প্যাকেজ পরিচালনা করুন
uv pip install -r backend/requirements.txt
```

### ২. ব্যাকএন্ড ও পিডব্লিউএ (PWA) চালু করুন
```powershell
& backend\.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port 8000 --reload
```
এখন আপনার ব্রাউজারে প্রবেশ করুন:
👉 **http://localhost:8000** — সরাসরি সই (Shoi) অ্যাপটি চালু হবে!
👉 **http://localhost:8000/docs** — সম্পূর্ণ ইন্টারেক্টিভ Swagger API ডকস।

---

## 🧪 টেস্ট চালান (Automated Test Suite)
প্রজেক্টের সমস্ত ভয়েস প্রসেসিং, মেমোরি রিটেনশন, নিরাপত্তা, প্রাইভেসি স্ক্রাবার, ক্লিনিক্যাল রুলস ও PWA টেস্ট করতে চালান:

```powershell
& backend\.venv\Scripts\python.exe -m pytest backend/tests
```
*ফলাফল: ৫৩টি টেস্টই সফলভাবে উত্তীর্ণ (53 passed, 100% pass rate in ~14s).*

---

## 🐳 ডকার দিয়ে ডিপ্লয়মেন্ট (Docker Deployment)
```bash
docker-compose up --build -d
```

---

## 📁 ফোল্ডার কাঠামো (Directory Layout)
```
CoU/
├── backend/
│   ├── app/
│   │   ├── api/            # /voice, /chat, /pcos, /track, /preg, /safety, /auth
│   │   ├── core/           # security, privacy PII scrubbers, logging filters
│   │   ├── db/             # SQLAlchemy session & database engine
│   │   ├── models/         # SQLAlchemy pseudonymous schema with cascade deletion
│   │   ├── schemas/        # Pydantic v2 strict data contracts
│   │   ├── services/       # session_memory, tts, chitchat, rag, cycle_engine,
│   │   │                   # mood_engine, pregnancy_engine, crisis_detector, pcos_model
│   │   └── main.py         # FastAPI application, PWA static mounts, CORS & headers
│   ├── ml/
│   │   ├── pcos/           # train.py, model.joblib (93.7% accuracy)
│   │   └── crisis/         # keywords_bn.json (direct, indirect, banglish)
│   ├── knowledge_base/     # WHO & DGHS curated facts
│   └── tests/              # 53 automated unit & integration tests
│       ├── test_voice_chat.py              # Long-horizon memory, dialect normalization, TTS cache
│       ├── test_pwa_real_life.py           # PWA manifest, service-worker, HTML DOM integrity
│       ├── test_emotional_intelligence.py  # Conversational empathy & warm sisterly tone
│       ├── test_safety.py                  # Crisis triggers & helpline escalation
│       ├── test_privacy.py                 # Zero-PII scrubbing & GDPR compliance
│       ├── test_cycle_engine.py            # FIGO menstrual cycle prediction
│       ├── test_pregnancy.py               # Naegele rule EDD & danger signs
│       ├── test_pcos.py                    # PCOS risk scoring
│       ├── test_mood_engine.py             # Mood tracking & PMS correlations
│       ├── test_auth.py                    # Anonymous pseudonymous tokens
│       ├── test_validations.py             # Input sanitization
│       ├── test_reminders.py               # Cycle alerts
│       └── test_integration.py            # End-to-end full system flow
├── pwa/                    # Mobile-First Progressive Web App (HTML, CSS, JS, Service Worker, Icons)
│   ├── icon.svg            # Vector app logo
│   ├── icon-192.png        # 192x192 maskable mobile icon
│   ├── icon-512.png        # 512x512 splash mobile icon
│   ├── manifest.json       # W3C Web App Manifest
│   ├── service-worker.js   # Offline cache strategy v2
│   ├── style.css           # Responsive mobile UI styling
│   └── app.js              # Client state, audio equalizer, voice barge-in, chips
├── mobile/                 # Flutter mobile codebase (pubspec.yaml, screens, widgets)
├── docs/                   # architecture.md, privacy-policy-bn.md, safety-protocol.md, evaluation-plan.md
└── docker-compose.yml
```

---

## 🛡️ সুরক্ষা ও নৈতিকতা (Ethics & Safeguards)
- সই কোনোভাবেই ডাক্তারের বিকল্প নয়।
- ওষুধ বা ড্রাগ ডোজ দেওয়ার উপর কঠোর নিষেধাজ্ঞা রয়েছে।
- কোনো ব্যক্তিগত পরিচিতি সংরক্ষণ করা হয় না।
