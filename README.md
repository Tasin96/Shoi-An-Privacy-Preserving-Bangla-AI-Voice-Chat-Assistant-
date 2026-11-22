# Shoi (সই) — গ্রামীণ নারীদের জন্য কৃত্রিম বুদ্ধিমত্তাভিত্তিক ভয়েস স্বাস্থ্য সহকারী

> **Privacy-preserving Bangla AI voice chat assistant for menstrual health and mental wellness among rural and semi-urban women.**

---

## 🌸 মূল বৈশিষ্ট্যসমূহ (Core Features)

1. **ভয়েস-ফার্স্ট ও সহজ বাংলা (Voice-First & Bangla-First):**
   - কম সাক্ষর নারীদের জন্য বড় মাইক্রোফোন বোতাম।
   - প্রাকৃতিক বাংলা কণ্ঠস্বর (Natural Bangla Neural Voice) দিয়ে স্বয়ংক্রিয় উত্তর পাঠ।
   - কথ্য ও আঞ্চলিক বাংলা শব্দের নির্ভুল বোঝাপড়া।

2. **সম্পূর্ণ গোপনীয় ও নিরাপদ (Zero-PII Privacy):**
   - কোনো নাম, মোবাইল নম্বর বা ইমেইল সংগ্রহ করা হয় না।
   - সম্পূর্ণ বেনামী র‍্যান্ডম আইডি (Anonymous UUID) দ্বারা পরিচালিত।
   - সার্ভার লগ থেকে স্বয়ংক্রিয়ভাবে আইপি (IP address) ও ফোন নম্বর মুছে দেওয়া হয়।
   - অডিও রূপান্তরের পর তাৎক্ষণিকভাবে মূল অডিও ধ্বংস করা হয়।
   - **"সব তথ্য মুছে ফেলুন" (Wipe All Data):** এক ক্লিকে সার্ভার ও ডিভাইস থেকে চিরতরে সমস্ত তথ্য মুছে ফেলার সুবিধা।

3. **মাসিক ও মেজাজ ট্র্যাকার (Period & Mood Tracker):**
   - মাসিকের চক্রের হিসাব, সম্ভাব্য পরবর্তী তারিখ এবং ওভুলেশন সময়ের পূর্বাভাস।
   - ৫টি সহজ ইমোজি দিয়ে প্রতিদিনের মনের অনুভূতি রেকর্ড ও পিএমএস (PMS) বিশ্লেষণ।

4. **পিসিওএস স্বাস্থ্য ঝুঁকি স্ক্রিনিং (PCOS Risk Screening):**
   - ল্যাব টেস্ট ছাড়া সাধারণ লক্ষণ ও অভ্যাসের ভিত্তিতে প্রশিক্ষিত মেশিন লার্নিং মডেল (Random Forest Classifier: 93.7% Accuracy, 0.978 ROC-AUC)।
   - স্ক্রিনিং ফলাফল কখনোই কোনো ডায়াগনোসিস নয়; সবসময় চিকিৎসকের পরামর্শ নেওয়ার দিকনির্দেশনা দেওয়া হয়।

5. **গর্ভকালীন যত্ন ও সময়রেখা (Pregnancy Care & Timeline):**
   - শেষ মাসিকের তারিখ (LMP) থেকে সপ্তাহ ও সম্ভাব্য প্রসব তারিখ (EDD) নির্ণয়।
   - সপ্তাহ অনুযায়ী শিশুর বৃদ্ধি এবং **৫টি মারাত্মক গর্ভকালীন বিপদচিহ্ন** প্রদর্শন।

6. **বহুস্তরী জরুরি মানসিক স্বাস্থ্য সুরক্ষা (Crisis Guardrails & 999 Trigger):**
   - আত্মহত্যা বা চরম হতাশার লক্ষণ ধরা পড়লে সরাসরি শান্ত সমর্থনমূলক স্ক্রিন ও **৯৯৯ (জাতীয় জরুরি সেবা)** ও **১০৯ (নারী নির্যাতন সেল)** এ সহজে কল করার বোতাম।

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
প্রজেক্টের সমস্ত মডিউল, নিরাপত্তা, প্রাইভেসি স্ক্রাবার ও ট্র্যাকার টেস্ট করতে চালান:

```powershell
& backend\.venv\Scripts\python.exe -m pytest
```
*ফলাফল: ১৯টি টেস্টই সফলভাবে উত্তীর্ণ হয়েছে (19 passed).*

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
│   │   ├── core/           # security, privacy PII filters
│   │   ├── models/         # SQLAlchemy pseudonymous schema
│   │   ├── schemas/        # Pydantic v2 validation models
│   │   ├── services/       # cycle_engine, mood_engine, pregnancy_engine, crisis_detector, pcos_model, rag, llm, asr, tts
│   │   └── main.py
│   ├── ml/
│   │   ├── pcos/           # train.py, model.joblib (93.7% accuracy)
│   │   └── crisis/         # keywords_bn.json (direct, indirect, banglish)
│   ├── knowledge_base/     # WHO & DGHS curated facts
│   └── tests/              # 19 automated pytest tests
├── pwa/                    # Mobile-First Progressive Web App (HTML, CSS, JS, Service Worker)
├── mobile/                 # Complete Flutter codebase (pubspec.yaml, screens, widgets)
├── docs/                   # architecture.md, privacy-policy-bn.md, safety-protocol.md, evaluation-plan.md
└── docker-compose.yml
```

---

## 🛡️ সুরক্ষা ও নৈতিকতা (Ethics & Safeguards)
- সই কোনোভাবেই ডাক্তারের বিকল্প নয়।
- ওষুধ বা ড্রাগ ডোজ দেওয়ার উপর কঠোর নিষেধাজ্ঞা রয়েছে।
- কোনো ব্যক্তিগত পরিচিতি সংরক্ষণ করা হয় না।
