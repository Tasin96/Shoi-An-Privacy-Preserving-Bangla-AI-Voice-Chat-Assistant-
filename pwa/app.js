// Shoi Frontend PWA Application Logic
const API_BASE = window.location.origin;

// State
let token = localStorage.getItem('shoi_token') || null;
let userId = localStorage.getItem('shoi_user_id') || null;
let sessionId = localStorage.getItem('shoi_session_id') || ('shoi_sess_' + Math.random().toString(36).substring(2, 12));
localStorage.setItem('shoi_session_id', sessionId);
let lastAudioBase64 = null;
let lastReplyText = null;
let recognition = null;
let mediaRecorder = null;
let audioChunks = [];
let isRecording = false;
let toastTimeout = null;

// DOM Elements
const micBtn = document.getElementById('micBtn');
const micWave = document.getElementById('micWave');
const voiceStatus = document.getElementById('voiceStatus');
const voiceStatusText = document.getElementById('voiceStatusText');
const micInstruction = document.getElementById('micInstruction');
const voiceResponseCard = document.getElementById('voiceResponseCard');
const userQueryBubble = document.getElementById('userQueryBubble');
const userQueryText = document.getElementById('userQueryText');
const responseText = document.getElementById('responseText');
const citationsContainer = document.getElementById('citationsContainer');
const audioPlayer = document.getElementById('audioPlayer');
const replayVoiceBtn = document.getElementById('replayVoiceBtn');
const emergencyModal = document.getElementById('emergencyModal');

// Non-blocking UI Toast
function showToast(message, isError = false) {
  let toast = document.getElementById('shoiToast');
  if (!toast) {
    toast = document.createElement('div');
    toast.id = 'shoiToast';
    toast.className = 'shoi-toast';
    document.body.appendChild(toast);
  }
  toast.textContent = message;
  toast.className = 'shoi-toast' + (isError ? ' error' : '');
  void toast.offsetWidth; // Trigger reflow for smooth animation
  toast.classList.add('show');

  if (toastTimeout) clearTimeout(toastTimeout);
  toastTimeout = setTimeout(() => {
    toast.classList.remove('show');
  }, 3200);
}

// Unlock audio context on user gesture to avoid browser autoplay blocks
function primeAudioPlayback() {
  if (audioPlayer && audioPlayer.paused && !audioPlayer.src) {
    audioPlayer.src = 'data:audio/wav;base64,UklGRigAAABXQVZFZm10IBIAAAABAAEARKwAAIhYAQACABAAAABkYXRhAgAAAAEA';
    audioPlayer.play().then(() => {
      audioPlayer.pause();
      audioPlayer.currentTime = 0;
    }).catch(() => {});
  }
}

// Initialize App
document.addEventListener('DOMContentLoaded', async () => {
  // Register Service Worker for PWA offline caching
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/pwa/service-worker.js').catch((err) => {
      console.log('SW registration note:', err);
    });
  }

  setupNavigation();
  setupSpeechAndAudioPipeline();
  await ensureAnonymousAuth();
  setupPeriodTracker();
  setupMoodTracker();
  setupPCOSChecker();
  setupPregnancyTracker();
  setupSettings();
  setupQuickQuestions();
});

// Helper for auth headers
function getAuthHeaders() {
  const headers = { 'Content-Type': 'application/json' };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  return headers;
}

// 1. Anonymous Authentication
async function ensureAnonymousAuth() {
  if (!token || !userId) {
    try {
      const res = await fetch(`${API_BASE}/auth/anonymous`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ age_group: '20-29', language: 'bn' })
      });
      if (res.ok) {
        const data = await res.json();
        token = data.access_token;
        userId = data.user_id;
        localStorage.setItem('shoi_token', token);
        localStorage.setItem('shoi_user_id', userId);
      }
    } catch (e) {
      console.warn('Anonymous auth offline/error:', e);
    }
  }

  const idDisplay = document.getElementById('anonymousUserIdDisplay');
  if (idDisplay && userId) {
    idDisplay.value = userId;
  }
}

// 2. Navigation Tabs
function setupNavigation() {
  const navItems = document.querySelectorAll('.nav-item');
  const screens = document.querySelectorAll('.screen');

  navItems.forEach(item => {
    item.addEventListener('click', () => {
      primeAudioPlayback();
      const targetId = item.getAttribute('data-target');

      navItems.forEach(n => n.classList.remove('active'));
      screens.forEach(s => s.classList.remove('active'));

      item.classList.add('active');
      const targetScreen = document.getElementById(targetId);
      if (targetScreen) targetScreen.classList.add('active');

      // Trigger refreshes for active tab
      if (targetId === 'screen-period') loadPeriodData();
      if (targetId === 'screen-mood') loadMoodData();
      if (targetId === 'screen-pregnancy') loadPregnancyData();
    });
  });

  // Emergency quick button
  document.getElementById('emergencyTriggerBtn').addEventListener('click', () => {
    emergencyModal.style.display = 'flex';
  });
  document.getElementById('dismissEmergencyBtn').addEventListener('click', () => {
    emergencyModal.style.display = 'none';
  });
}

// 3. Voice & Speech Recognition Pipeline (Dual: Web Speech API + MediaRecorder Fallback)
function setupSpeechAndAudioPipeline() {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

  if (SpeechRecognition) {
    recognition = new SpeechRecognition();
    recognition.lang = 'bn-BD'; // Standard Bangla
    recognition.continuous = false;
    recognition.interimResults = false;

    recognition.onstart = () => {
      isRecording = true;
      setVoiceState('listening');
    };

    recognition.onresult = async (event) => {
      const transcript = event.results[0][0].transcript;
      console.log('Recognized speech:', transcript);
      setVoiceState('thinking');
      await sendVoiceQuery(transcript);
    };

    recognition.onerror = (event) => {
      console.warn('Speech recognition status:', event.error);
      isRecording = false;
      setVoiceState('idle');
      if (event.error === 'not-allowed') {
        showToast('মাইক্রোফোন ব্যবহারের অনুমতি দিন।', true);
      } else if (event.error === 'no-speech') {
        voiceStatusText.textContent = 'কোনো কথা শোনা যায়নি। আবার বোতাম চেপে বলুন।';
      }
    };

    recognition.onend = () => {
      isRecording = false;
      if (voiceStatus.className.includes('listening')) {
        setVoiceState('idle');
      }
    };
  }

  micBtn.addEventListener('click', async () => {
    primeAudioPlayback();

    // If currently speaking, interrupt and stop audio immediately
    if (voiceStatus.className.includes('speaking')) {
      if (audioPlayer) {
        audioPlayer.pause();
        audioPlayer.currentTime = 0;
      }
      if ('speechSynthesis' in window) {
        window.speechSynthesis.cancel();
      }
      setVoiceState('idle');
      return;
    }

    // If currently recording, stop
    if (isRecording) {
      if (recognition) {
        try { recognition.stop(); } catch (e) {}
      }
      if (mediaRecorder && mediaRecorder.state === 'recording') {
        mediaRecorder.stop();
      }
      isRecording = false;
      setVoiceState('thinking');
      return;
    }

    // Start recording
    if (recognition) {
      try {
        recognition.start();
        return;
      } catch (e) {
        console.warn('Recognition start failed, trying MediaRecorder:', e);
      }
    }

    // MediaRecorder fallback (Firefox, Safari, WebViews)
    if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        audioChunks = [];
        mediaRecorder = new MediaRecorder(stream);
        
        mediaRecorder.ondataavailable = (event) => {
          if (event.data.size > 0) audioChunks.push(event.data);
        };

        mediaRecorder.onstop = async () => {
          stream.getTracks().forEach(track => track.stop());
          const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
          if (audioBlob.size > 0) {
            setVoiceState('thinking');
            await sendVoiceAudio(audioBlob);
          } else {
            setVoiceState('idle');
          }
        };

        mediaRecorder.start();
        isRecording = true;
        setVoiceState('listening');
      } catch (err) {
        console.error('Microphone access denied or unavailable:', err);
        showToast('মাইক্রোফোন চালু করা সম্ভব হয়নি। অনুগ্রহ করে অনুমতি দিন বা লিখে জানান।', true);
        setVoiceState('idle');
      }
    } else {
      // Manual input toggle if audio capture is completely unsupported
      const chatDrawer = document.getElementById('textChatDrawer');
      if (chatDrawer) chatDrawer.style.display = 'block';
      showToast('আপনার ব্রাউজারে ভয়েস সমর্থিত নয়। নিচে লিখে প্রশ্ন করুন।');
    }
  });

  // Replay audio
  replayVoiceBtn.addEventListener('click', () => {
    primeAudioPlayback();
    if (lastAudioBase64) {
      audioPlayer.src = `data:audio/mp3;base64,${lastAudioBase64}`;
      setVoiceState('speaking');
      audioPlayer.play().catch(() => setVoiceState('idle'));
      audioPlayer.onended = () => setVoiceState('idle');
    } else if (lastReplyText && 'speechSynthesis' in window) {
      speakNativeText(lastReplyText);
    }
  });

  // Text chat drawer toggle
  const toggleBtn = document.getElementById('toggleTextChatBtn');
  const chatDrawer = document.getElementById('textChatDrawer');
  const chatInput = document.getElementById('chatInput');
  const sendBtn = document.getElementById('sendChatBtn');

  toggleBtn.addEventListener('click', () => {
    primeAudioPlayback();
    const isHidden = chatDrawer.style.display === 'none';
    chatDrawer.style.display = isHidden ? 'block' : 'none';
    toggleBtn.textContent = isHidden ? '❌ চ্যাট বন্ধ করুন' : '⌨️ লিখে জিজ্ঞাসা করুন';
    if (isHidden) chatInput.focus();
  });

  sendBtn.addEventListener('click', () => {
    primeAudioPlayback();
    const text = chatInput.value.trim();
    if (text) {
      chatInput.value = '';
      setVoiceState('thinking');
      sendVoiceQuery(text);
    }
  });

  chatInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
      sendBtn.click();
    }
  });
}

function setVoiceState(state) {
  voiceStatus.className = 'voice-status-pill ' + state;
  micWave.className = 'mic-wave' + (state === 'listening' ? ' active' : (state === 'speaking' ? ' speaking' : ''));

  if (state === 'listening') {
    voiceStatusText.textContent = 'শুনছি... আপনার প্রশ্ন বলুন';
    micInstruction.textContent = 'কথা শেষ হলে বোতামে আবার চাপ দিন';
  } else if (state === 'thinking') {
    voiceStatusText.textContent = 'ভাবছি... একটু অপেক্ষা করুন';
    micInstruction.textContent = 'তথ্য যাচাই করা হচ্ছে...';
  } else if (state === 'speaking') {
    voiceStatusText.textContent = 'বলছি... শুনুন';
    micInstruction.textContent = 'থামাতে বোতামে আবার চাপ দিন';
  } else {
    voiceStatusText.textContent = 'কথা বলতে বোতামে চাপ দিন';
    micInstruction.textContent = 'মাঝের বোতামটি চেপে আপনার প্রশ্ন বলুন';
  }
}

async function sendVoiceQuery(textQuery) {
  try {
    const res = await fetch(`${API_BASE}/voice`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Session-ID': sessionId
      },
      body: JSON.stringify({
        direct_transcript: textQuery,
        session_id: sessionId
      })
    });

    if (res.ok) {
      const data = await res.json();
      if (data.session_id) {
        sessionId = data.session_id;
        localStorage.setItem('shoi_session_id', sessionId);
      }
      displayVoiceResponse(data);
    } else {
      setVoiceState('idle');
      showToast('উত্তর পেতে সমস্যা হয়েছে। আবার চেষ্টা করুন।', true);
    }
  } catch (err) {
    console.error('Voice query error:', err);
    setVoiceState('idle');
    showToast('নেটওয়ার্ক সংযোগ নেই বা ত্রুটি দেখা দিয়েছে।', true);
  }
}

async function sendVoiceAudio(audioBlob) {
  try {
    const formData = new FormData();
    formData.append('audio_file', audioBlob, 'voice_query.webm');
    formData.append('session_id', sessionId);

    const res = await fetch(`${API_BASE}/voice`, {
      method: 'POST',
      headers: {
        'X-Session-ID': sessionId
      },
      body: formData
    });

    if (res.ok) {
      const data = await res.json();
      if (data.session_id) {
        sessionId = data.session_id;
        localStorage.setItem('shoi_session_id', sessionId);
      }
      displayVoiceResponse(data);
    } else {
      setVoiceState('idle');
      showToast('ভয়েস প্রক্রিয়াকরণে সমস্যা হয়েছে। আবার চেষ্টা করুন।', true);
    }
  } catch (err) {
    console.error('Voice audio upload error:', err);
    setVoiceState('idle');
    showToast('ভয়েস পাঠাতে সমস্যা হয়েছে।', true);
  }
}

function cleanBanglaPhonetics(text) {
  if (!text) return '';
  // Remove citations & system notes
  let t = text.replace(/\([^\)]*সূত্র[^\)]*\)/g, '').replace(/\[[^\]]*সূত্র[^\]]*\]/g, '');
  t = t.replace(/\(সূত্র:[^\)]*\)/g, '');
  
  // English acronyms to Bangla phonetics
  t = t.replace(/\bPCOS\b|\bpcos\b/gi, 'পিসিওএস');
  t = t.replace(/\bBMI\b|\bbmi\b/gi, 'বিএমআই');
  t = t.replace(/\bEDD\b|\bedd\b/gi, 'ইডিডি');
  t = t.replace(/\bLMP\b|\blmp\b/gi, 'এলএমপি');
  t = t.replace(/\bAI\b|\bai\b/gi, 'এআই');
  t = t.replace(/\bSMS\b|\bsms\b/gi, 'এসএমএস');
  t = t.replace(/\bWHO\b|\bwho\b/gi, 'হু');
  t = t.replace(/\bDGHS\b|\bdghs\b/gi, 'ডিজিএইচএস');
  t = t.replace(/\bDr\.?|\bdr\.?/gi, 'ডাক্তার');
  t = t.replace(/\bapp\b/gi, 'অ্যাপ');
  t = t.replace(/\b999\b/g, 'নয় নয় নয়');
  t = t.replace(/\b109\b/g, 'এক শূন্য নয়');

  // Convert English digits to Bengali digits
  const enToBn = {'0':'০','1':'১','2':'২','3':'৩','4':'৪','5':'৫','6':'৬','7':'৭','8':'৮','9':'৯'};
  t = t.replace(/[0-9]/g, digit => enToBn[digit] || digit);
  t = t.replace(/([০-৯]+)\s*[-–—]\s*([০-৯]+)/g, '$1 থেকে $2');

  // Remove markdown symbols
  t = t.replace(/[*#`~>\[\]]/g, '');
  t = t.replace(/[-–—]/g, ', ');
  return t.trim();
}

function speakNativeText(text) {
  if ('speechSynthesis' in window) {
    window.speechSynthesis.cancel();
    const cleanText = cleanBanglaPhonetics(text);
    const utterance = new SpeechSynthesisUtterance(cleanText);
    utterance.lang = 'bn-BD';
    
    // Pick the most natural female Bangla voice available
    const voices = window.speechSynthesis.getVoices();
    const bnVoice = voices.find(v => 
      v.lang === 'bn-BD' || 
      v.lang.startsWith('bn') || 
      v.name.includes('Bangla') || 
      v.name.includes('Bengali') || 
      v.name.includes('Nabanita')
    );
    if (bnVoice) utterance.voice = bnVoice;
    
    utterance.rate = 0.92;
    utterance.pitch = 1.0;
    
    setVoiceState('speaking');
    utterance.onend = () => setVoiceState('idle');
    utterance.onerror = () => setVoiceState('idle');
    window.speechSynthesis.speak(utterance);
  }
}

function displayVoiceResponse(data) {
  lastReplyText = data.reply_text;
  responseText.textContent = data.reply_text;
  voiceResponseCard.style.display = 'block';
  setTimeout(() => {
    voiceResponseCard.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  }, 100);

  // Display user query if transcript exists
  if (userQueryBubble && userQueryText) {
    if (data.transcript && data.transcript.trim()) {
      userQueryText.textContent = data.transcript;
      userQueryBubble.style.display = 'block';
    } else {
      userQueryBubble.style.display = 'none';
    }
  }

  // Citations
  if (data.citations && data.citations.length > 0) {
    citationsContainer.innerHTML = '<strong>তথ্যসূত্র:</strong> ' + data.citations.join(', ');
  } else {
    citationsContainer.innerHTML = '';
  }

  // Safety trigger
  const emergencyInlineBox = document.getElementById('emergencyInlineBox');
  if (data.risk_level === 'high' || (data.emergency_payload && data.emergency_payload.is_emergency)) {
    if (emergencyInlineBox) emergencyInlineBox.style.display = 'block';
    if (emergencyModal) emergencyModal.style.display = 'flex';
  } else {
    if (emergencyInlineBox) emergencyInlineBox.style.display = 'none';
  }

  // Audio Playback
  if (data.audio_base64) {
    lastAudioBase64 = data.audio_base64;
    audioPlayer.src = `data:audio/mp3;base64,${data.audio_base64}`;
    setVoiceState('speaking');
    audioPlayer.play().catch(() => {
      // If browser blocks autoplay, user can tap replay button
      setVoiceState('idle');
    });
    audioPlayer.onended = () => setVoiceState('idle');
  } else {
    speakNativeText(data.reply_text);
  }
}

function setupQuickQuestions() {
  document.querySelectorAll('.chip').forEach(chip => {
    chip.addEventListener('click', () => {
      primeAudioPlayback();
      const q = chip.getAttribute('data-q');
      setVoiceState('thinking');
      sendVoiceQuery(q);
    });
  });
}

// 4. Period Tracker Logic
function setupPeriodTracker() {
  const form = document.getElementById('periodForm');
  const startDateInput = document.getElementById('periodStartDate');
  const endDateInput = document.getElementById('periodEndDate');

  // Pre-fill today's date and enforce boundary
  const today = new Date().toISOString().split('T')[0];
  if (startDateInput) {
    startDateInput.value = today;
    startDateInput.max = today;
  }
  if (endDateInput) {
    endDateInput.max = today;
  }

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const startDate = startDateInput.value;
    const endDate = endDateInput.value || null;

    if (startDate > today) {
      showToast('ভবিষ্যতের তারিখ নির্বাচন করা যাবে না।', true);
      return;
    }

    if (endDate && endDate < startDate) {
      showToast('শেষের তারিখ শুরুর তারিখের আগের হতে পারে না।', true);
      return;
    }

    const flowInput = form.querySelector('input[name="flow"]:checked');
    const flow = flowInput ? flowInput.value : 'medium';

    // Scoped symptom selection
    const symptoms = [];
    form.querySelectorAll('.symptom-tags input:checked').forEach(cb => symptoms.push(cb.value));

    try {
      const res = await fetch(`${API_BASE}/track/period`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({ start_date: startDate, end_date: endDate, flow, symptoms })
      });
      if (res.ok) {
        showToast('পিরিয়ড সফলভাবে সংরক্ষণ করা হয়েছে!');
        // Reset inputs to clean defaults
        startDateInput.value = today;
        endDateInput.value = '';
        form.querySelectorAll('.symptom-tags input').forEach(cb => cb.checked = false);
        loadPeriodData();
      } else {
        const err = await res.json();
        showToast(err.detail || 'পিরিয়ড সংরক্ষণ ব্যর্থ হয়েছে', true);
      }
    } catch (e) {
      console.error(e);
      showToast('সার্ভারের সাথে যোগাযোগ করা যায়নি।', true);
    }
  });
}

async function loadPeriodData() {
  if (!token) return;
  try {
    const resAnalysis = await fetch(`${API_BASE}/track/period/analysis`, {
      headers: getAuthHeaders()
    });
    if (resAnalysis.ok) {
      const a = await resAnalysis.json();
      const infoBox = document.getElementById('predictionInfo');
      infoBox.innerHTML = `
        <p style="white-space: pre-line;">${a.explanation_bn}</p>
        ${a.predicted_next_period_start ? `<p style="margin-top: 8px;"><strong>পরবর্তী পিরিয়ড:</strong> ${a.predicted_next_period_start}</p>` : ''}
        ${a.ovulation_window_start ? `<p><strong>ডিম্বস্ফোটন সময়:</strong> ${a.ovulation_window_start} হতে ${a.ovulation_window_end}</p>` : ''}
      `;
    }

    const resList = await fetch(`${API_BASE}/track/period`, {
      headers: getAuthHeaders()
    });
    if (resList.ok) {
      const list = await resList.json();
      const ul = document.getElementById('periodList');
      if (list.length === 0) {
        ul.innerHTML = '<li>কোনো পূর্ববর্তী পিরিয়ড লগ নেই।</li>';
      } else {
        ul.innerHTML = list.map(item => `
          <li>
            <strong>শুরু:</strong> ${item.start_date} ${item.end_date ? `| <strong>শেষ:</strong> ${item.end_date}` : ''}
            <br><small>মাত্রা: ${item.flow === 'heavy' ? 'ভারী' : (item.flow === 'light' ? 'হালকা' : 'স্বাভাবিক')}, লক্ষণ: ${item.symptoms.join(', ') || 'নেই'}</small>
          </li>
        `).join('');
      }
    }
  } catch (e) {
    console.error(e);
  }
}

// 5. Mood Tracker Logic
let selectedMoodScore = 3;

function setupMoodTracker() {
  const emojiBtns = document.querySelectorAll('.emoji-btn');
  
  // Ensure default score 3 has selected class on load
  emojiBtns.forEach(btn => {
    if (parseInt(btn.getAttribute('data-score')) === selectedMoodScore) {
      btn.classList.add('selected');
    }
    btn.addEventListener('click', () => {
      emojiBtns.forEach(b => b.classList.remove('selected'));
      btn.classList.add('selected');
      selectedMoodScore = parseInt(btn.getAttribute('data-score'));
    });
  });

  document.getElementById('saveMoodBtn').addEventListener('click', async () => {
    const tags = [];
    document.querySelectorAll('#moodTags input:checked').forEach(cb => tags.push(cb.value));

    try {
      const res = await fetch(`${API_BASE}/track/mood`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({ mood_score: selectedMoodScore, tags })
      });
      if (res.ok) {
        showToast('আপনার অনুভূতি সংরক্ষণ করা হয়েছে!');
        loadMoodData();
      } else {
        showToast('অনুভূতি সংরক্ষণ করা সম্ভব হয়নি।', true);
      }
    } catch (e) {
      console.error(e);
      showToast('সার্ভারের সাথে যোগাযোগ করা যায়নি।', true);
    }
  });
}

async function loadMoodData() {
  if (!token) return;
  try {
    const res = await fetch(`${API_BASE}/track/mood/analysis`, {
      headers: getAuthHeaders()
    });
    if (res.ok) {
      const a = await res.json();
      const p = document.getElementById('moodSuggestionText');
      p.innerHTML = `
        ${a.seven_day_avg ? `<p>৭ দিনের গড় মেজাজ: <strong>${a.seven_day_avg} / ৫</strong></p>` : ''}
        ${a.phase_correlation_bn ? `<p style="color: #9E3E5B; margin: 6px 0;"><strong>${a.phase_correlation_bn}</strong></p>` : ''}
        <p style="margin-top: 8px;">${a.gentle_suggestion_bn}</p>
      `;
    }
  } catch (e) {
    console.error(e);
  }
}

// 6. PCOS Risk Checker Logic
function setupPCOSChecker() {
  const form = document.getElementById('pcosForm');
  const quizCard = document.getElementById('pcosQuizCard');
  const resultCard = document.getElementById('pcosResultCard');

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const payload = {
      age: parseInt(document.getElementById('pcosAge').value),
      height_cm: parseFloat(document.getElementById('pcosHeight').value),
      weight_kg: parseFloat(document.getElementById('pcosWeight').value),
      cycle_regularity: document.querySelector('input[name="cycle_regularity"]:checked').value,
      cycle_length_days: parseInt(document.getElementById('pcosCycleLength').value),
      weight_gain: document.getElementById('pcosWeightGain').checked,
      excess_hair_growth: document.getElementById('pcosHairGrowth').checked,
      skin_darkening: document.getElementById('pcosSkinDark').checked,
      hair_loss: document.getElementById('pcosHairLoss').checked,
      pimples_acne: document.getElementById('pcosAcne').checked,
      regular_exercise: document.querySelector('input[name="pcosExercise"]:checked').value === 'yes'
    };

    try {
      const res = await fetch(`${API_BASE}/pcos/predict`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify(payload)
      });
      if (res.ok) {
        const result = await res.json();
        displayPCOSResult(result);
      } else {
        showToast('পিসিওএস ফলাফল পাওয়া যায়নি। আবার চেষ্টা করুন।', true);
      }
    } catch (e) {
      console.error(e);
      showToast('সার্ভারের সাথে যোগাযোগ করা যায়নি।', true);
    }
  });

  document.getElementById('pcosRetakeBtn').addEventListener('click', () => {
    resultCard.style.display = 'none';
    quizCard.style.display = 'block';
  });
}

function displayPCOSResult(res) {
  document.getElementById('pcosQuizCard').style.display = 'none';
  const resultCard = document.getElementById('pcosResultCard');
  resultCard.style.display = 'block';

  const badge = document.getElementById('pcosRiskBadge');
  badge.textContent = res.risk_band_bn;
  badge.className = `result-badge ${res.risk_band}`;

  document.getElementById('pcosExplanation').textContent = res.explanation_bn;

  const factorsUl = document.getElementById('pcosFactorsList');
  factorsUl.innerHTML = res.contributing_factors.map(f => `<li>${f}</li>`).join('');

  const adviceUl = document.getElementById('pcosAdviceList');
  adviceUl.innerHTML = res.actionable_advice_bn.map(a => `<li>${a}</li>`).join('');

  document.getElementById('pcosDisclaimer').textContent = res.disclaimer_bn;
}

// 7. Pregnancy Tracker Logic
function setupPregnancyTracker() {
  const saveBtn = document.getElementById('savePregBtn');
  const lmpInput = document.getElementById('pregLmpDate');

  // Enforce boundary
  const today = new Date().toISOString().split('T')[0];
  if (lmpInput) {
    lmpInput.max = today;
  }

  saveBtn.addEventListener('click', async () => {
    const lmp = lmpInput.value;
    if (!lmp) {
      showToast('অনুগ্রহ করে শেষ মাসিকের প্রথম দিন নির্বাচন করুন', true);
      return;
    }
    if (lmp > today) {
      showToast('ভবিষ্যতের তারিখ নির্বাচন করা যাবে না।', true);
      return;
    }

    try {
      const res = await fetch(`${API_BASE}/preg/start`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({ lmp_date: lmp })
      });
      if (res.ok) {
        const data = await res.json();
        renderPregnancyStatus(data);
        showToast('গর্ভকালীন তথ্য সফলভাবে আপডেট হয়েছে!');
      } else {
        const err = await res.json();
        showToast(err.detail || 'তথ্য প্রক্রিয়াকরণে সমস্যা হয়েছে', true);
      }
    } catch (e) {
      console.error(e);
      showToast('সার্ভারের সাথে যোগাযোগ করা যায়নি।', true);
    }
  });
}

async function loadPregnancyData() {
  if (!token) return;
  try {
    const res = await fetch(`${API_BASE}/preg/timeline`, {
      headers: getAuthHeaders()
    });
    if (res.ok) {
      const data = await res.json();
      renderPregnancyStatus(data);
      // Pre-fill LMP date input
      const lmpInput = document.getElementById('pregLmpDate');
      if (lmpInput && data.lmp_date) {
        lmpInput.value = data.lmp_date;
      }
    }
  } catch (e) {
    console.warn('No active pregnancy found');
  }
}

function renderPregnancyStatus(data) {
  const card = document.getElementById('pregStatusCard');
  card.style.display = 'block';

  document.getElementById('pregWeeks').textContent = data.gestational_weeks;
  document.getElementById('pregTrimester').textContent = data.current_trimester + (data.current_trimester === 1 ? 'ম' : (data.current_trimester === 2 ? 'য়' : 'য়'));
  document.getElementById('pregEdd').textContent = data.edd;

  const m = data.current_milestone;
  document.getElementById('pregBabySize').textContent = `শিশুর আকার: ${m.baby_size_bn}`;
  document.getElementById('pregDevelopment').textContent = m.development_summary_bn;
  document.getElementById('pregMotherChanges').textContent = m.maternal_changes_bn;

  const ancBox = document.getElementById('pregAncNotice');
  if (m.anc_recommended && m.anc_visit_title_bn) {
    ancBox.innerHTML = `<strong>🩺 চেকআপ সময়:</strong> ${m.anc_visit_title_bn}`;
    ancBox.style.display = 'block';
  } else {
    ancBox.style.display = 'none';
  }

  const dangerUl = document.getElementById('pregDangerSigns');
  dangerUl.innerHTML = m.urgent_warning_signs_bn.map(s => `<li>${s}</li>`).join('');
}

// 8. Settings Logic
function setupSettings() {
  const copyBtn = document.getElementById('copyIdBtn');
  copyBtn.addEventListener('click', () => {
    const idField = document.getElementById('anonymousUserIdDisplay');
    idField.select();
    navigator.clipboard.writeText(idField.value);
    showToast('আইডি কপি করা হয়েছে!');
  });

  // Save PIN button
  const savePinBtn = document.getElementById('savePinBtn');
  const pinInput = document.getElementById('userPinInput');
  if (savePinBtn && pinInput) {
    savePinBtn.addEventListener('click', async () => {
      const pin = pinInput.value.trim();
      if (!/^\d{4,6}$/.test(pin)) {
        showToast('পিন অবশ্যই ৪ থেকে ৬ সংখ্যার (শুধু সংখ্যা) হতে হবে', true);
        return;
      }
      try {
        const res = await fetch(`${API_BASE}/auth/pin`, {
          method: 'PUT',
          headers: getAuthHeaders(),
          body: JSON.stringify({ pin })
        });
        if (res.ok) {
          showToast('পিন কোড সফলভাবে সংরক্ষিত হয়েছে!');
          pinInput.value = '';
        } else {
          showToast('পিন সংরক্ষণ করতে সমস্যা হয়েছে।', true);
        }
      } catch (e) {
        console.error(e);
        showToast('সার্ভারের সাথে যোগাযোগ করা যায়নি।', true);
      }
    });
  }

  const deleteBtn = document.getElementById('deleteAllDataBtn');
  deleteBtn.addEventListener('click', async () => {
    if (confirm('আপনি কি নিশ্চিত যে আপনার সমস্ত তথ্য চিরতরে মুছে ফেলতে চান? এটি আর ফিরিয়ে আনা যাবে না।')) {
      try {
        const res = await fetch(`${API_BASE}/auth/me`, {
          method: 'DELETE',
          headers: getAuthHeaders()
        });
        if (res.ok) {
          showToast('আপনার সমস্ত তথ্য সফলভাবে মুছে ফেলা হয়েছে।');
          localStorage.clear();
          setTimeout(() => {
            window.location.reload();
          }, 1200);
        } else {
          showToast('তথ্য মুছতে সমস্যা হয়েছে।', true);
        }
      } catch (e) {
        console.error(e);
        showToast('সার্ভারের সাথে যোগাযোগ করা যায়নি।', true);
      }
    }
  });
}
