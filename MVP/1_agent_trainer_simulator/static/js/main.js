// JavaScript Logic for AI Agent Trainer Simulator

let currentSessionId = null;
let currentProfileId = 'subsidized_rate';
let currentGender = 'male';
let isListening = false;
let recognition = null;
let lastEvaluation = null;

// Emojis and Russian titles for client emotional states
const EMOTIONS_MAP = {
    'skeptical': { emoji: '🤨', title: 'Скептичный', class: 'emotion-skeptical' },
    'angry': { emoji: '😡', title: 'Раздраженный', class: 'emotion-angry' },
    'neutral': { emoji: '😐', title: 'Нейтральный', class: 'emotion-neutral' },
    'interested': { emoji: '😊', title: 'Заинтересован', class: 'emotion-interested' },
    'satisfied': { emoji: '🤝', title: 'Доволен', class: 'emotion-satisfied' }
};

// Map profiles to Russian names for avatars
const PROFILE_NAMES = {
    'subsidized_rate': 'Михаил',
    'waiting_rates': 'Сергей',
    'investor_yield': 'Рамиль',
    'tranche_risk': 'Ольга',
    'artur_rent': 'Артур',
    'maria_expansion': 'Мария',
    'igor_investment': 'Игорь'
};

// Initialize Speech Recognition
function initSpeechRecognition() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
        console.warn("Web Speech API (Recognition) is not supported in this browser.");
        document.getElementById('btn-mic').style.display = 'none';
        document.getElementById('mic-status-label').innerText = "Голосовой ввод не поддерживается вашим браузером (рекомендуется Chrome/Safari).";
        document.getElementById('mic-status-label').classList.add('show');
        return;
    }
    
    recognition = new SpeechRecognition();
    recognition.lang = 'ru-RU';
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;
    
    recognition.onstart = () => {
        isListening = true;
        const micBtn = document.getElementById('btn-mic');
        micBtn.classList.add('listening');
        const statusLabel = document.getElementById('mic-status-label');
        statusLabel.innerText = "Слушаю вас... Говорите";
        statusLabel.classList.add('show');
    };
    
    recognition.onend = () => {
        isListening = false;
        document.getElementById('btn-mic').classList.remove('listening');
        document.getElementById('mic-status-label').classList.remove('show');
    };
    
    recognition.onerror = (event) => {
        console.error("Speech recognition error:", event.error);
        isListening = false;
        document.getElementById('btn-mic').classList.remove('listening');
        const statusLabel = document.getElementById('mic-status-label');
        statusLabel.innerText = `Ошибка записи: ${event.error}`;
        statusLabel.classList.add('show');
        setTimeout(() => statusLabel.classList.remove('show'), 3000);
    };
    
    recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        const inputField = document.getElementById('user-input');
        inputField.value = transcript;
        sendMessage(); // Automatically send after voice dictation
    };
}

// Toggle Voice Input (Microphone)
function toggleSpeechInput() {
    if (!recognition) return;
    
    if (isListening) {
        recognition.stop();
    } else {
        recognition.start();
    }
}

// Speak Text using Web Speech Synthesis
function speakText(text) {
    const isVoiceMode = document.getElementById('voice-mode-checkbox').checked;
    if (!isVoiceMode) return;
    
    // Stop any current speaking
    window.speechSynthesis.cancel();
    
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = 'ru-RU';
    
    // Find Russian voices
    const voices = window.speechSynthesis.getVoices();
    const ruVoices = voices.filter(v => v.lang.startsWith('ru'));
    
    if (ruVoices.length > 0) {
        // Simple heuristic for male/female voice selection
        let selectedVoice = null;
        if (currentGender === 'female') {
            // Try to find a female sounding voice
            selectedVoice = ruVoices.find(v => v.name.toLowerCase().includes('google') || v.name.toLowerCase().includes('microsoft') || v.name.toLowerCase().includes('milena') || v.name.toLowerCase().includes('premium')) || ruVoices[0];
        } else {
            // Try to find a male voice
            selectedVoice = ruVoices.find(v => v.name.toLowerCase().includes('pavel') || v.name.toLowerCase().includes('alexander') || v.name.toLowerCase().includes('google')) || ruVoices[0];
        }
        
        if (selectedVoice) {
            utterance.voice = selectedVoice;
        }
    }
    
    // Voice configurations
    utterance.rate = 1.0; 
    utterance.pitch = currentGender === 'female' ? 1.1 : 0.95;
    
    window.speechSynthesis.speak(utterance);
}

// Switch Scenario
function selectScenario(profileId, element) {
    document.querySelectorAll('.scenario-card').forEach(c => c.classList.remove('active'));
    element.classList.add('active');
    currentProfileId = profileId;
    startNewSession();
}

// Start Simulator Session
async function startNewSession() {
    const chatBox = document.getElementById('chat-box');
    chatBox.innerHTML = '<div class="message system-msg">Запуск симуляции клиента...</div>';
    
    // Reset controls state
    lastEvaluation = null;
    document.getElementById('btn-evaluate').style.display = 'inline-flex';
    
    try {
        const response = await fetch('/api/start', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ profile_id: currentProfileId })
        });
        const data = await response.json();
        
        if (data.error) {
            chatBox.innerHTML = `<div class="message system-msg" style="color:var(--color-danger)">Ошибка запуска: ${data.error}</div>`;
            return;
        }
        
        currentSessionId = data.session_id;
        currentGender = data.gender || 'male';
        chatBox.innerHTML = '';
        
        // Update client info in header
        const clientName = PROFILE_NAMES[currentProfileId] || 'Клиент';
        document.getElementById('active-client-name').innerText = clientName;
        document.getElementById('client-avatar-img').innerText = currentGender === 'female' ? '👩' : '👨';
        
        updateSentiment('neutral', 3);
        
        // Add client greeting message
        addMessage(data.greeting, 'client');
        
        // Speak greeting if voice mode is enabled
        setTimeout(() => speakText(data.greeting), 600);
        
    } catch (e) {
        chatBox.innerHTML = `<div class="message system-msg" style="color:var(--color-danger)">Ошибка сети при запуске: ${e.message}</div>`;
    }
}

// Add message to Chat Box
function addMessage(text, sender, emotion = null) {
    const chatBox = document.getElementById('chat-box');
    
    // Remove typing indicator if any
    const typing = document.getElementById('client-typing');
    if (typing) chatBox.removeChild(typing);
    
    const msgDiv = document.createElement('div');
    msgDiv.className = `message ${sender}`;
    
    if (sender === 'client' && emotion) {
        const emotionMeta = EMOTIONS_MAP[emotion] || EMOTIONS_MAP['neutral'];
        const metaSpan = document.createElement('div');
        metaSpan.className = 'message-meta';
        metaSpan.innerHTML = `<span style="font-size: 0.72rem; opacity:0.8; margin-right: 5px">${emotionMeta.emoji}</span>`;
        msgDiv.appendChild(metaSpan);
    }
    
    const textSpan = document.createElement('span');
    textSpan.innerText = text;
    msgDiv.appendChild(textSpan);
    
    chatBox.appendChild(msgDiv);
    chatBox.scrollTop = chatBox.scrollHeight;
}

// Show Typing Indicator
function showTypingIndicator() {
    const chatBox = document.getElementById('chat-box');
    
    // Remove if already exists
    const existing = document.getElementById('client-typing');
    if (existing) chatBox.removeChild(existing);
    
    const typingDiv = document.createElement('div');
    typingDiv.className = 'message client';
    typingDiv.id = 'client-typing';
    typingDiv.innerHTML = `
        <div class="typing-indicator">
            <span></span>
            <span></span>
            <span></span>
        </div>
    `;
    chatBox.appendChild(typingDiv);
    chatBox.scrollTop = chatBox.scrollHeight;
}

// Send Message to backend
async function sendMessage() {
    const input = document.getElementById('user-input');
    const text = input.value.trim();
    if (!text || !currentSessionId) return;

    // Speak synthesize cancellation
    window.speechSynthesis.cancel();

    addMessage(text, 'broker');
    input.value = '';

    showTypingIndicator();

    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ session_id: currentSessionId, message: text })
        });
        const data = await response.json();
        
        // Remove typing
        const typing = document.getElementById('client-typing');
        if (typing) document.getElementById('chat-box').removeChild(typing);
        
        if (data.reply) {
            addMessage(data.reply, 'client', data.emotion);
            updateSentiment(data.emotion, data.sentiment_score);
            speakText(data.reply);
        } else if (data.error) {
            addMessage(`[Ошибка бэкенда]: ${data.error}`, 'client', 'angry');
            updateSentiment('angry', 1);
        }
    } catch (e) {
        const typing = document.getElementById('client-typing');
        if (typing) document.getElementById('chat-box').removeChild(typing);
        addMessage(`[Ошибка сети]: ${e.message}`, 'client', 'angry');
        updateSentiment('angry', 1);
    }
}

// Update Active Client Emotional Status in Header
function updateSentiment(emotion, score) {
    const badge = document.getElementById('client-sentiment-badge');
    const indicator = document.getElementById('sentiment-indicator');
    
    const info = EMOTIONS_MAP[emotion] || EMOTIONS_MAP['neutral'];
    
    // Reset classes
    badge.className = 'client-sentiment-badge';
    badge.classList.add(info.class);
    badge.innerText = `${info.emoji} ${info.title}`;
    
    // Update indicator dot color
    let dotColor = '#94a3b8'; // neutral
    if (emotion === 'satisfied') dotColor = '#10b981';
    else if (emotion === 'interested') dotColor = '#3b82f6';
    else if (emotion === 'skeptical') dotColor = '#f59e0b';
    else if (emotion === 'angry') dotColor = '#ef4444';
    
    indicator.style.backgroundColor = dotColor;
    indicator.style.boxShadow = `0 0 8px ${dotColor}`;
}

// Keyboard keypress capture
function handleKeyPress(e) {
    if (e.key === 'Enter') {
        sendMessage();
    }
}

// Restart Simulation Session
function restartSession() {
    if (confirm("Вы действительно хотите начать тренировку заново? Прогресс текущего диалога сотрется.")) {
        startNewSession();
    }
}

// Close Evaluation Modal
function closeModal() {
    document.getElementById('overlay').classList.remove('active');
}

// Tab navigation within the evaluation dashboard modal
function switchEvalTab(tabId) {
    document.querySelectorAll('.eval-tab-btn').forEach(btn => btn.classList.remove('active'));
    document.querySelectorAll('.eval-tab-content').forEach(content => content.classList.remove('active'));
    
    document.querySelector(`[data-tab="${tabId}"]`).classList.add('active');
    document.getElementById(tabId).classList.add('active');
}

// Perform dialogue evaluation
async function evaluateSession() {
    if (!currentSessionId) return;
    
    // Open modal and show loading state
    document.getElementById('overlay').classList.add('active');
    const container = document.getElementById('eval-result-container');
    container.innerHTML = `
        <div style="display:flex; flex-direction:column; align-items:center; justify-content:center; padding:4rem; gap:1.5rem;">
            <div class="typing-indicator" style="transform:scale(2)">
                <span style="background-color:var(--accent-cyan)"></span>
                <span style="background-color:var(--accent-purple)"></span>
                <span style="background-color:var(--accent-cyan)"></span>
            </div>
            <div style="text-align:center; color:var(--text-secondary); font-family:var(--font-heading); font-size:1.1rem; font-weight:500;">
                🧙‍♂️ ИИ-Бизнес-тренер анализирует ваш диалог... <br>
                <span style="font-size:0.85rem; color:var(--text-muted); font-weight:400; margin-top:0.5rem; display:inline-block;">Проверяем соответствие критериям чек-листа первого касания</span>
            </div>
        </div>
    `;
    
    // Clear save state button
    const saveBtn = document.getElementById('btn-save-obsidian');
    saveBtn.disabled = false;
    saveBtn.innerHTML = `
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/>
            <polyline points="17 21 17 13 7 13 7 21"/>
            <polyline points="7 3 7 8 15 8"/>
        </svg>
        <span>Сохранить в Obsidian</span>
    `;
    
    try {
        const response = await fetch('/api/evaluate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ session_id: currentSessionId })
        });
        const data = await response.json();
        
        if (data.error) {
            container.innerHTML = `<div class="message system-msg" style="color:var(--color-danger)">Ошибка оценки: ${data.error}</div>`;
            return;
        }
        
        lastEvaluation = data.evaluation;
        renderEvaluationDashboard(data.evaluation);
        
    } catch (e) {
        container.innerHTML = `<div class="message system-msg" style="color:var(--color-danger)">Ошибка соединения с сервером: ${e.message}</div>`;
    }
}

// Render dynamic dashboard components from JSON evaluation
function renderEvaluationDashboard(evalData) {
    const container = document.getElementById('eval-result-container');
    const clientName = PROFILE_NAMES[currentProfileId] || 'Клиент';
    
    document.getElementById('eval-subtitle').innerText = `Сценарий: ${clientName} (${CLIENT_PROFILES[currentProfileId].title})`;
    
    // HTML structure for Dashboard
    let html = `
        <!-- Hero Summary -->
        <div class="eval-hero">
            <div class="score-circle-container">
                <svg class="score-circle-svg" viewBox="0 0 100 100">
                    <circle class="score-circle-bg" cx="50" cy="50" r="40"></circle>
                    <circle class="score-circle-fill" id="gauge-fill" cx="50" cy="50" r="40"></circle>
                    <defs>
                        <linearGradient id="score-gradient" x1="0%" y1="0%" x2="100%" y2="100%">
                            <stop offset="0%" stop-color="#8b5cf6"></stop>
                            <stop offset="100%" stop-color="#06b6d4"></stop>
                        </linearGradient>
                    </defs>
                </svg>
                <div class="score-text">
                    <span id="score-val">0</span>
                    <span class="score-total">из 10</span>
                </div>
            </div>
            
            <div class="eval-summary">
                <h4>Резюме бизнес-тренера</h4>
                <p>${evalData.summary}</p>
            </div>
        </div>
        
        <!-- Navigation Tabs -->
        <nav class="eval-tabs-nav">
            <button class="eval-tab-btn active" data-tab="tab-checklist" onclick="switchEvalTab('tab-checklist')">📋 Чек-лист первого касания</button>
            <button class="eval-tab-btn" data-tab="tab-analysis" onclick="switchEvalTab('tab-analysis')">💡 Сильные стороны и Ошибки</button>
            <button class="eval-tab-btn" data-tab="tab-speech" onclick="switchEvalTab('tab-speech')">🛠️ Спич-анализ (Как надо говорить)</button>
        </nav>
        
        <!-- Tab 1: Checklist -->
        <div class="eval-tab-content active" id="tab-checklist">
            <div class="checklist-results">
    `;
    
    evalData.criteria.forEach(crit => {
        let badgeClass = 'badge-neutral';
        let statusTitle = crit.status;
        
        if (crit.status === 'Passed') {
            badgeClass = 'badge-passed';
            statusTitle = 'Выполнено';
        } else if (crit.status === 'Partially') {
            badgeClass = 'badge-partially';
            statusTitle = 'Частично';
        } else if (crit.status === 'Failed') {
            badgeClass = 'badge-failed';
            statusTitle = 'Не выполнено';
        }
        
        html += `
            <div class="checklist-result-card">
                <div class="crit-left">
                    <div class="crit-name">${crit.name}</div>
                    <div class="crit-comment">${crit.comment}</div>
                </div>
                <div class="crit-badge ${badgeClass}">${statusTitle}</div>
            </div>
        `;
    });
    
    html += `
            </div>
        </div>
        
        <!-- Tab 2: Strengths & Weaknesses -->
        <div class="eval-tab-content" id="tab-analysis">
            <div class="strengths-weaknesses-grid">
                <div class="eval-col-card col-strengths">
                    <div class="col-title">
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
                            <polyline points="22 4 12 14.01 9 11.01"/>
                        </svg>
                        Сильные стороны
                    </div>
                    <ul class="bullets-list">
    `;
    
    evalData.strengths.forEach(str => {
        html += `<li>${str}</li>`;
    });
    
    html += `
                    </ul>
                </div>
                
                <div class="eval-col-card col-weaknesses">
                    <div class="col-title">
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                            <circle cx="12" cy="12" r="10"/>
                            <line x1="15" y1="9" x2="9" y2="15"/>
                            <line x1="9" y1="9" x2="15" y2="15"/>
                        </svg>
                        Ошибки и зоны роста
                    </div>
                    <ul class="bullets-list">
    `;
    
    evalData.weaknesses.forEach(weak => {
        html += `<li>${weak}</li>`;
    });
    
    html += `
                    </ul>
                </div>
            </div>
            
            <div class="recommendations-box">
                <h4>
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41"/>
                    </svg>
                    Рекомендации по улучшению
                </h4>
                <ul>
    `;
    
    evalData.recommendations.forEach(rec => {
        html += `<li>${rec}</li>`;
    });
    
    html += `
                </ul>
            </div>
        </div>
        
        <!-- Tab 3: Speech Analysis -->
        <div class="eval-tab-content" id="tab-speech">
            <div class="speech-analyses">
    `;
    
    if (!evalData.best_responses || evalData.best_responses.length === 0) {
        html += `<div style="text-align:center; color:var(--text-muted); padding:2rem;">Разбор конкретных реплик не потребовался. Брокер провел отличный диалог!</div>`;
    } else {
        evalData.best_responses.forEach(resp => {
            html += `
                <div class="speech-card">
                    <div class="speech-row original">
                        <div class="speech-label">Как сказал Брокер</div>
                        <div class="speech-text">"${resp.broker_original}"</div>
                    </div>
                    <div class="speech-row improved">
                        <div class="speech-label">Как сказать лучше (Метод anton-voice)</div>
                        <div class="speech-text">"${resp.broker_improved}"</div>
                    </div>
                    <div class="speech-row rationale">
                        <div class="speech-label">Почему это работает</div>
                        <div class="speech-text">${resp.rationale}</div>
                    </div>
                </div>
            `;
        });
    }
    
    html += `
            </div>
        </div>
        
        <!-- Obsidian placeholder container -->
        <div id="obsidian-save-status"></div>
    `;
    
    container.innerHTML = html;
    
    // Animate score counter and radial gauge progress
    setTimeout(() => {
        // Circle stroke math: r=40, circumference = 2 * PI * r = 251.2
        const percentage = evalData.total_score / 10;
        const offset = 251.2 - (percentage * 251.2);
        
        const fillCircle = document.getElementById('gauge-fill');
        if (fillCircle) {
            fillCircle.style.strokeDashoffset = offset;
        }
        
        // Counter animation
        let count = 0;
        const interval = setInterval(() => {
            if (count >= evalData.total_score) {
                clearInterval(interval);
            } else {
                count += 0.5;
                document.getElementById('score-val').innerText = count.toFixed(1).replace('.0', '');
            }
        }, 50);
    }, 100);
}

// Save Report to Obsidian via backend API
async function saveReportToObsidian() {
    if (!currentSessionId || !lastEvaluation) return;
    
    const saveBtn = document.getElementById('btn-save-obsidian');
    saveBtn.disabled = true;
    saveBtn.innerHTML = `
        <svg class="typing-indicator" style="width:18px; height:18px; margin:0;" viewBox="0 0 24 24" fill="none" stroke="currentColor">
            <circle cx="12" cy="12" r="10" stroke-width="2" stroke-dasharray="16" style="animation:spin 1s linear infinite;"/>
        </svg>
        <span>Сохраняю...</span>
    `;
    
    try {
        const response = await fetch('/api/save_report', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                session_id: currentSessionId,
                evaluation: lastEvaluation
            })
        });
        const data = await response.json();
        
        const statusBox = document.getElementById('obsidian-save-status');
        
        if (data.success) {
            saveBtn.innerHTML = `
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <polyline points="20 6 9 17 4 12"/>
                </svg>
                <span>Сохранено!</span>
            `;
            
            statusBox.innerHTML = `
                <div class="save-success-box">
                    <div class="left">
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="var(--color-success)" stroke-width="2.5">
                            <polyline points="20 6 9 17 4 12"/>
                        </svg>
                        <span>Отчет сохранен в Obsidian: <strong>${data.filename}</strong></span>
                    </div>
                    <a href="${data.obsidian_link}">Открыть в Obsidian</a>
                </div>
            `;
        } else {
            saveBtn.disabled = false;
            saveBtn.innerHTML = `<span>Попробовать снова</span>`;
            alert(`Ошибка сохранения: ${data.error}`);
        }
    } catch (e) {
        saveBtn.disabled = false;
        saveBtn.innerHTML = `<span>Попробовать снова</span>`;
        alert(`Ошибка подключения при сохранении: ${e.message}`);
    }
}

// Window load handler
window.onload = () => {
    // Populate client voices on load if voice synthesis supports it
    if (window.speechSynthesis) {
        window.speechSynthesis.onvoiceschanged = () => {};
    }
    
    initSpeechRecognition();
    startNewSession();
};
