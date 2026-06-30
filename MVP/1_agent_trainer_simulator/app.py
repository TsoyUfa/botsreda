import os
import json
from flask import Flask, request, jsonify, render_template_string
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables
load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

app = Flask(__name__)

# Configure Gemini
api_key = os.getenv("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)
else:
    print("Warning: GEMINI_API_KEY is not set. Please update the .env file.")

# Local profiles
CLIENT_PROFILES = {
    "subsidized_rate": {
        "title": "Субсидия — это развод",
        "description": "Клиент считает, что субсидированная ставка (например, 3% или 5%) — это обман, так как застройщик сильно завышает базовую стоимость квартиры.",
        "prompt": "Ты — сложный, сомневающийся клиент по имени Михаил. Ты хочешь купить квартиру, но брокер предлагает тебе субсидированную ставку. Ты убежден, что это развод и маркетинговый ход: застройщик просто накинул 20% к стоимости квартиры, чтобы сделать красивую ставку. Ты общаешься с брокером настороженно, задаешь каверзные вопросы про реальную переплату, не веришь словам на слово, требуешь цифр. Не соглашайся сразу, спорь, требуй объяснить выгоду. Твои реплики должны быть естественными для переписки (1-3 предложения)."
    },
    "waiting_rates": {
        "title": "Подожду снижения ставок",
        "description": "Клиент считает, что текущие рыночные ставки по ипотеке грабительские, и планирует арендовать или ждать, пока ЦБ снизит ставку.",
        "prompt": "Ты — клиент по имени Сергей. Ты присматриваешь жилье, но считаешь, что покупать квартиру сейчас — это безумие из-за высоких ставок по ипотеке. Ты говоришь брокеру: 'Я лучше подожду год-два, пока ставки снизятся, или буду пока снимать'. Ты убежден, что переплачивать по 18-20% годовых глупо. Задача брокера — показать тебе альтернативные варианты (рассрочки, транши, субсидии). Ты споришь, защищаешь позицию ожидания. Отвечай как обычный человек в мессенджере (коротко, скептично)."
    },
    "investor_yield": {
        "title": "Инвестор: сомнения в росте",
        "description": "Инвестор ищет доходность 20% годовых, считает рынок новостроек перегретым и не верит в рост конкретного ЖК.",
        "prompt": "Ты — прагматичный инвестор по имени Рамиль. У тебя есть свободные средства, ты ищешь доходность от 20% годовых на перепродаже или аренде. Ты считаешь рынок новостроек сильно надутым пузырем и говоришь брокеру, что цены падут, а конкретный ЖК, который он предлагает — переоценен. Ты общаешься профессионально, оперируешь терминами (ROI, окупаемость, первоначальный взнос), требуешь четких финансовых расчетов. Не поддавайся на эмоции, только жесткие цифры и выгода."
    },
    "tranche_risk": {
        "title": "Траншевая ипотека — это риск",
        "description": "Клиент боится траншевой ипотеки (платеж частями), считает её сложной и боится банкротства застройщика.",
        "prompt": "Ты — клиент по имени Ольга. Ты очень осторожна и боишься потерять деньги. Брокер предлагает тебе схему с траншевой ипотекой (когда кредит выдается частями по 1 рублю или 10% до сдачи дома). Тебе это кажется мутной схемой. Ты переживаешь: 'А вдруг застройщик обанкротится? А вдруг банк откажет во втором транше? Почему все так сложно?'. Ты хочешь простую классическую покупку, но у тебя не хватает денег на большой ежемесячный платеж. Брокер должен успокоить тебя и разложить безопасность эскроу-счетов. Сомневайся, бойся рисков."
    }
}

# In-memory storage for active sessions
sessions = {}

def get_checklist():
    """Load Checklist from Obsidian vault if exists, otherwise fallback to default."""
    vault_path = os.getenv("OBSIDIAN_VAULT_PATH", "/Users/anton_tsoy/Desktop/Обсидиан")
    checklist_file = os.path.join(
        vault_path,
        "6. обучения агентов/1. Опытные агенты/Блоки обучения/1 блок (от касания до экскурсии)/Чек лист первого касания.md"
    )
    if os.path.exists(checklist_file):
        try:
            with open(checklist_file, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            return f"Error reading checklist file: {e}"
    
    # Default fallback checklist
    return """
# Чек-лист первого касания (оценка брокера):
1. **Установление контакта:** Поздоровался, представился, уточнил имя клиента, создал комфортную атмосферу (без давления).
2. **Квалификация и выявление болей:** Задал открытые вопросы. Узнал реальную мотивацию покупки (инвестиции, для себя, расширение).
3. **Отработка возражения / Финансовый инжиниринг:** Не спорил напрямую, применил технику согласия (Да, я согласен, что ставки высокие, и именно поэтому...). Предложил альтернативные финансовые схемы (транши, рассрочки, субсидии).
4. **Экспертная позиция (anton-voice):** Объяснял простыми словами, оперировал цифрами, не пытался "впарить" квартиру, вел диалог с позиции партнера (win-win).
5. **Закрытие на следующий шаг:** Четко договорился о следующем действии (встреча, отправка расчетов в мессенджер, созвон в конкретное время).
"""

@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE, profiles=CLIENT_PROFILES)

@app.route("/api/start", methods=["POST"])
def start_session():
    data = request.json or {}
    profile_id = data.get("profile_id")
    if profile_id not in CLIENT_PROFILES:
        return jsonify({"error": "Invalid profile ID"}), 400
    
    session_id = os.urandom(8).hex()
    profile = CLIENT_PROFILES[profile_id]
    
    sessions[session_id] = {
        "profile_id": profile_id,
        "history": [
            {"role": "system", "content": profile["prompt"]}
        ],
        "chat_history": [] # Only client/broker messages
    }
    
    # Generate first greeting from client
    client_greeting = "Здравствуйте! Я по поводу квартиры, которую вы предлагали."
    if profile_id == "subsidized_rate":
        client_greeting = "Добрый день! Посмотрел ваш расчет с ипотекой под 3%. Скажите честно, в чем тут подвох? Опять застройщик цену накинул?"
    elif profile_id == "waiting_rates":
        client_greeting = "Приветствую! Квартиры интересные, но при текущих ставках по ипотеке я, пожалуй, повременю. Буду пока снимать или подожду, пока ставки упадут."
    elif profile_id == "investor_yield":
        client_greeting = "Здравствуйте. Ищу объект под инвестиции, но у вас цены перегреты. Какая тут реальная доходность с учетом переплаты? Не вижу смысла входить сейчас."
    elif profile_id == "tranche_risk":
        client_greeting = "Здравствуйте. Вы мне прислали схему с траншевой ипотекой по 10 тысяч в месяц до сдачи дома. Звучит заманчиво, но мне страшно. Это вообще законно? Что если застройщик обанкротится?"

    sessions[session_id]["history"].append({"role": "model", "content": client_greeting})
    sessions[session_id]["chat_history"].append({"sender": "client", "text": client_greeting})
    
    return jsonify({"session_id": session_id, "greeting": client_greeting})

@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.json or {}
    session_id = data.get("session_id")
    message = data.get("message", "").strip()
    
    if session_id not in sessions:
        return jsonify({"error": "Session not found"}), 404
    if not message:
        return jsonify({"error": "Empty message"}), 400
        
    session = sessions[session_id]
    
    # Add broker message
    session["history"].append({"role": "user", "content": message})
    session["chat_history"].append({"sender": "broker", "text": message})
    
    # If API key is not configured, return mock reply
    if not api_key:
        reply = f"[Имитация ответа клиента {session['profile_id']}]: Я вас услышал, но все равно сомневаюсь. Объясните подробнее."
        session["history"].append({"role": "model", "content": reply})
        session["chat_history"].append({"sender": "client", "text": reply})
        return jsonify({"reply": reply})
        
    try:
        # Prepare content for Gemini API
        # We transform history to Gemini format (role: user/model)
        contents = []
        for h in session["history"]:
            # Gemini GenerativeModel Chat expects user and model roles. System instructions go to system_instruction
            if h["role"] == "system":
                continue
            role = "user" if h["role"] == "user" else "model"
            contents.append({"role": role, "parts": [h["content"]]})
            
        model = genai.GenerativeModel(
            model_name='gemini-1.5-flash',
            system_instruction=CLIENT_PROFILES[session["profile_id"]]["prompt"]
        )
        
        response = model.generate_content(contents)
        reply = response.text.strip()
        
        # Save model reply
        session["history"].append({"role": "model", "content": reply})
        session["chat_history"].append({"sender": "client", "text": reply})
        
        return jsonify({"reply": reply})
    except Exception as e:
        return jsonify({"error": f"Gemini API error: {str(e)}"}), 500

@app.route("/api/evaluate", methods=["POST"])
def evaluate():
    data = request.json or {}
    session_id = data.get("session_id")
    
    if session_id not in sessions:
        return jsonify({"error": "Session not found"}), 404
        
    session = sessions[session_id]
    dialogue_formatted = ""
    for msg in session["chat_history"]:
        role_name = "Брокер" if msg["sender"] == "broker" else "Клиент"
        dialogue_formatted += f"{role_name}: {msg['text']}\n"
        
    checklist_content = get_checklist()
    
    evaluation_prompt = f"""
Ты — профессиональный бизнес-тренер по продажам недвижимости и эксперт по методологии Антона Цоя. Твоя задача — объективно оценить диалог брокера с клиентом.

Вот текст диалога:
\"\"\"
{dialogue_formatted}
\"\"\"

Вот критерии оценки (чек-лист первого касания из Obsidian):
\"\"\"
{checklist_content}
\"\"\"

Составь отчет по следующим пунктам:
1. **Общая оценка (от 1 до 10)** и краткое резюме беседы.
2. **Анализ выполнения чек-листа** (по каждому пункту: пройдено/не пройдено/частично и почему).
3. **Сильные стороны брокера** (что сделано отлично, какие реплики удачные).
4. **Ошибки и зоны роста** (где свалился в оправдания, где не дожал, где спорил с клиентом напрямую).
5. **Конкретные рекомендации по улучшению** (как переписать неудачные реплики, какие цифры стоило привести).

Ответ верни строго в красивой разметке Markdown (используй списки, жирный шрифт, цитаты).
"""
    
    if not api_key:
        mock_eval = f"""### 📊 Имитация оценки диалога (API Ключ не задан)
* **Общая оценка:** 7/10
* **Анализ чек-листа:**
  * Установление контакта: Выполнено.
  * Выявление болей: Частично (мало открытых вопросов).
  * Финансовый инжиниринг: Сделана попытка предложить схему, но без цифр.
* **Рекомендация:** Укажи реальные платежи в рублях, чтобы клиент увидел выгоду.
"""
        return jsonify({"evaluation": mock_eval})
        
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(evaluation_prompt)
        evaluation_text = response.text.strip()
        
        return jsonify({"evaluation": evaluation_text})
    except Exception as e:
        return jsonify({"error": f"Evaluation error: {str(e)}"}), 500

# HTML Template as single string for zero-file-dependency simplicity
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ИИ-Тренажер Брокера — MVP 1</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-color: #0b0f19;
            --card-bg: rgba(22, 30, 49, 0.7);
            --card-border: rgba(255, 255, 255, 0.06);
            --text-primary: #f8fafc;
            --text-secondary: #94a3b8;
            --accent-primary: #8b5cf6;
            --accent-secondary: #06b6d4;
            --font-main: 'Inter', sans-serif;
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            background-color: var(--bg-color);
            color: var(--text-primary);
            font-family: var(--font-main);
            height: 100vh;
            display: flex;
            background-image: 
                radial-gradient(circle at 10% 20%, rgba(139, 92, 246, 0.06) 0%, transparent 40%),
                radial-gradient(circle at 90% 80%, rgba(6, 166, 212, 0.06) 0%, transparent 40%);
            overflow: hidden;
        }

        /* Sidebar */
        .sidebar {
            width: 320px;
            background: rgba(15, 23, 42, 0.6);
            border-right: 1px solid var(--card-border);
            padding: 1.5rem;
            display: flex;
            flex-direction: column;
            gap: 1.5rem;
        }

        .logo {
            font-size: 1.25rem;
            font-weight: 700;
            background: linear-gradient(135deg, #ffffff 0%, var(--accent-secondary) 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 1rem;
        }

        .scenarios-list {
            display: flex;
            flex-direction: column;
            gap: 1rem;
            flex-grow: 1;
            overflow-y: auto;
        }

        .scenario-card {
            background: rgba(255, 255, 255, 0.02);
            border: 1px solid var(--card-border);
            border-radius: 12px;
            padding: 1rem;
            cursor: pointer;
            transition: all 0.2s ease;
        }

        .scenario-card:hover {
            background: rgba(255, 255, 255, 0.05);
            border-color: rgba(6, 182, 212, 0.3);
        }

        .scenario-card.active {
            background: rgba(139, 92, 246, 0.1);
            border-color: var(--accent-primary);
        }

        .scenario-card h3 {
            font-size: 0.95rem;
            font-weight: 600;
            margin-bottom: 0.25rem;
        }

        .scenario-card p {
            font-size: 0.8rem;
            color: var(--text-secondary);
            line-height: 1.4;
        }

        /* Main Workspace */
        .workspace {
            flex-grow: 1;
            display: flex;
            flex-direction: column;
            height: 100%;
        }

        header {
            padding: 1.25rem 2rem;
            border-bottom: 1px solid var(--card-border);
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: rgba(15, 23, 42, 0.3);
        }

        h2 {
            font-size: 1.15rem;
            font-weight: 600;
        }

        .btn {
            background: var(--accent-primary);
            color: white;
            border: none;
            padding: 0.6rem 1.2rem;
            border-radius: 8px;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s;
            font-size: 0.9rem;
        }

        .btn:hover {
            opacity: 0.9;
            transform: translateY(-1px);
        }

        .btn-evaluate {
            background: var(--accent-secondary);
        }

        /* Chat Area */
        .chat-area {
            flex-grow: 1;
            padding: 2rem;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 1.25rem;
        }

        .message {
            max-width: 70%;
            padding: 1rem;
            border-radius: 14px;
            line-height: 1.5;
            font-size: 0.92rem;
        }

        .message.client {
            background: rgba(255, 255, 255, 0.04);
            border: 1px solid var(--card-border);
            align-self: flex-start;
            border-top-left-radius: 2px;
        }

        .message.broker {
            background: var(--accent-primary);
            color: white;
            align-self: flex-end;
            border-top-right-radius: 2px;
        }

        /* Input Bar */
        .input-bar {
            padding: 1.5rem 2rem;
            border-top: 1px solid var(--card-border);
            background: rgba(15, 23, 42, 0.4);
            display: flex;
            gap: 1rem;
        }

        input {
            flex-grow: 1;
            background: rgba(0, 0, 0, 0.2);
            border: 1px solid var(--card-border);
            border-radius: 10px;
            padding: 0.8rem 1.2rem;
            color: white;
            font-family: var(--font-main);
            font-size: 0.95rem;
        }

        input:focus {
            outline: none;
            border-color: var(--accent-secondary);
        }

        /* Modal Overlay for Evaluation */
        .overlay {
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            background: rgba(11, 15, 25, 0.85);
            backdrop-filter: blur(10px);
            display: flex;
            justify-content: center;
            align-items: center;
            z-index: 100;
            opacity: 0;
            pointer-events: none;
            transition: opacity 0.3s ease;
        }

        .overlay.active {
            opacity: 1;
            pointer-events: auto;
        }

        .modal {
            background: #111827;
            border: 1px solid var(--card-border);
            border-radius: 20px;
            width: 90%;
            max-width: 800px;
            max-height: 85vh;
            padding: 2rem;
            display: flex;
            flex-direction: column;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.5);
        }

        .modal-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid var(--card-border);
            padding-bottom: 1rem;
            margin-bottom: 1.5rem;
        }

        .modal-body {
            overflow-y: auto;
            flex-grow: 1;
            font-size: 0.95rem;
            line-height: 1.6;
            color: #cbd5e1;
        }

        /* Markdown styling inside modal */
        .modal-body h3 {
            color: white;
            margin: 1.2rem 0 0.6rem 0;
            font-size: 1.1rem;
        }

        .modal-body ul, .modal-body ol {
            margin-left: 1.5rem;
            margin-bottom: 1rem;
        }

        .modal-body li {
            margin-bottom: 0.4rem;
        }

        .modal-body blockquote {
            border-left: 4px solid var(--accent-primary);
            padding-left: 1rem;
            margin: 1rem 0;
            font-style: italic;
            color: var(--text-secondary);
        }
    </style>
</head>
<body>
    <!-- Sidebar Scenarios -->
    <div class="sidebar">
        <div class="logo">⚡ ИИ-Тренажер Брокера</div>
        <div class="scenarios-list">
            {% for key, val in profiles.items() %}
            <div class="scenario-card {% if loop.first %}active{% endif %}" onclick="selectScenario('{{ key }}', this)">
                <h3>{{ val.title }}</h3>
                <p>{{ val.description }}</p>
            </div>
            {% endfor %}
        </div>
    </div>

    <!-- Chat Area -->
    <div class="workspace">
        <header>
            <h2 id="scenario-title">Сценарий: Загрузка...</h2>
            <button class="btn btn-evaluate" onclick="evaluateSession()">📊 Оценить диалог</button>
        </header>

        <div class="chat-area" id="chat-box">
            <!-- Messages go here -->
        </div>

        <div class="input-bar">
            <input type="text" id="user-input" placeholder="Введите ваш ответ клиенту..." onkeypress="handleKeyPress(event)">
            <button class="btn" onclick="sendMessage()">Отправить</button>
        </div>
    </div>

    <!-- Modal for Evaluation -->
    <div class="overlay" id="overlay" onclick="closeModal()">
        <div class="modal" onclick="event.stopPropagation()">
            <div class="modal-header">
                <h2>📊 Аналитический отчет и оценка диалога</h2>
                <button class="btn" style="background: rgba(255,255,255,0.05); color: white; border: 1px solid var(--card-border);" onclick="closeModal()">Закрыть</button>
            </div>
            <div class="modal-body" id="eval-result">
                Идет расчет оценок и анализ чек-листа...
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
    <script>
        let currentSessionId = null;
        let currentProfileId = 'subsidized_rate';

        function selectScenario(profileId, element) {
            document.querySelectorAll('.scenario-card').forEach(c => c.classList.remove('active'));
            element.classList.add('active');
            currentProfileId = profileId;
            startNewSession();
        }

        async function startNewSession() {
            const chatBox = document.getElementById('chat-box');
            chatBox.innerHTML = '<div style="color:var(--text-secondary); text-align:center;">Запуск симуляции клиента...</div>';
            
            try {
                const response = await fetch('/api/start', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ profile_id: currentProfileId })
                });
                const data = await response.json();
                
                currentSessionId = data.session_id;
                chatBox.innerHTML = '';
                addMessage(data.greeting, 'client');
                
                // Update title
                const activeCard = document.querySelector('.scenario-card.active h3');
                document.getElementById('scenario-title').innerText = `Клиент: ${activeCard.innerText}`;
            } catch (e) {
                chatBox.innerHTML = `<div style="color:#ef4444; text-align:center;">Ошибка запуска: ${e.message}</div>`;
            }
        }

        function addMessage(text, sender) {
            const chatBox = document.getElementById('chat-box');
            const msgDiv = document.createElement('div');
            msgDiv.className = `message ${sender}`;
            msgDiv.innerText = text;
            chatBox.appendChild(msgDiv);
            chatBox.scrollTop = chatBox.scrollHeight;
        }

        async function sendMessage() {
            const input = document.getElementById('user-input');
            const text = input.value.trim();
            if (!text || !currentSessionId) return;

            addMessage(text, 'broker');
            input.value = '';

            // Add loading placeholder from client
            const chatBox = document.getElementById('chat-box');
            const loadingDiv = document.createElement('div');
            loadingDiv.className = 'message client';
            loadingDiv.innerText = 'Печатает...';
            chatBox.appendChild(loadingDiv);
            chatBox.scrollTop = chatBox.scrollHeight;

            try {
                const response = await fetch('/api/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ session_id: currentSessionId, message: text })
                });
                const data = await response.json();
                
                chatBox.removeChild(loadingDiv);
                
                if (data.reply) {
                    addMessage(data.reply, 'client');
                } else if (data.error) {
                    addMessage(`[Ошибка]: ${data.error}`, 'client');
                }
            } catch (e) {
                chatBox.removeChild(loadingDiv);
                addMessage(`[Ошибка сети]: ${e.message}`, 'client');
            }
        }

        function handleKeyPress(e) {
            if (e.key === 'Enter') {
                sendMessage();
            }
        }

        async function evaluateSession() {
            if (!currentSessionId) return;
            
            document.getElementById('overlay').classList.add('active');
            const evalResult = document.getElementById('eval-result');
            evalResult.innerHTML = '<div style="text-align:center; padding:2rem;">🧙‍♂️ ИИ анализирует ваш диалог на соответствие чек-листу первого касания... Подождите несколько секунд.</div>';
            
            try {
                const response = await fetch('/api/evaluate', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ session_id: currentSessionId })
                });
                const data = await response.json();
                
                if (data.evaluation) {
                    // Use marked.js to render Markdown returned by API
                    evalResult.innerHTML = marked.parse(data.evaluation);
                } else {
                    evalResult.innerText = `Ошибка оценки: ${data.error}`;
                }
            } catch (e) {
                evalResult.innerText = `Ошибка сети при расчете оценки: ${e.message}`;
            }
        }

        function closeModal() {
            document.getElementById('overlay').classList.remove('active');
        }

        // Initialize on load
        window.onload = () => {
            startNewSession();
        };
    </script>
</body>
</html>
"""

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.getenv("PORT", 8000)), debug=True)
