import os
import glob
import shutil
from datetime import datetime
from dotenv import load_dotenv
import google.generativeai as genai

# Load env variables
load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

# Configuration
VAULT_PATH = os.getenv("OBSIDIAN_VAULT_PATH", "/Users/anton_tsoy/Desktop/Обсидиан")
INBOX_DIR = os.path.join(VAULT_PATH, "inbox")
ARCHIVE_DIR = os.path.join(os.path.dirname(__file__), "archive")

# Formats to check
AUDIO_EXTENSIONS = ["*.mp3", "*.wav", "*.m4a", "*.mp4", "*.aac"]

# Ensure directories exist
os.makedirs(INBOX_DIR, exist_ok=True)
os.makedirs(ARCHIVE_DIR, exist_ok=True)

# Configure Gemini
api_key = os.getenv("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)
else:
    print("Error: GEMINI_API_KEY is not configured in .env file.")
    exit(1)

def find_audio_files():
    files = []
    for ext in AUDIO_EXTENSIONS:
        files.extend(glob.glob(os.path.join(INBOX_DIR, ext)))
    return files

def summarize_audio(file_path):
    filename = os.path.basename(file_path)
    print(f"\n[+] Найдена аудиозапись: {filename}")
    print("[~] Загрузка файла в Gemini API...")
    
    try:
        # Upload the file to Gemini (Gemini handles transcription & analysis natively!)
        uploaded_file = genai.upload_file(path=file_path)
        print(f"[~] Файл загружен. Идентификатор в API: {uploaded_file.name}")
        print("[~] ИИ анализирует аудиозапись и генерирует конспект...")
        
        prompt = """
Ты — высококлассный ассистент-методолог и секретарь. Перед тобой аудиозапись встречи (планерки, обучения или созвона по недвижимости). 
Твоя задача — внимательно прослушать (или проанализировать) запись и составить структурированный конспект (митинг-минс) в формате Markdown.

Сформируй отчет по следующему шаблону:

# 🎙️ Оцифровка созвона: [Придумай емкое название темы разговора]

* **Дата обработки:** [Сегодняшняя дата]
* **Оригинальный файл:** [Имя файла]

---

## 📝 Краткое содержание встречи
[Напиши краткую выжимку в 3-5 предложений: о чем шла речь, какая главная цель встречи]

---

## ⚡ Поручения и задачи (Action Items)
Составь четкий список задач по итогам встречи. Если в аудио упоминаются имена, закрепи задачу за конкретным человеком.
*   [ ] **[Имя ответственного, если есть]**: [Суть задачи] — [Срок выполнения, если упоминался]
*   [ ] **[Имя ответственного]**: [Суть задачи]

---

## 🧠 Методологические инсайты и идеи (Методический блок Антона Цоя)
Вытащи из разговора ключевые мысли, которые можно использовать для обучения агентов или написания постов/Reels:
1.  **[Суть идеи/инсайта]**: Подробное описание концепта.
2.  **Заготовки под Reels/посты**: Были ли темы, из которых можно собрать контент?
3.  **Схемы / Расчеты**: Упоминались ли конкретные расчеты ипотек, рассрочек, траншей?

---

## ❌ Проблемные зоны и обсуждения
*   Какие возражения клиентов или трудности брокеров обсуждались?
*   Какие ошибки брокеров были зафиксированы?

---

Ответ верни строго на русском языке, в чистой разметке Markdown. Общайся уверенно, профессионально и по делу.
"""

        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content([prompt, uploaded_file])
        
        # Save output markdown
        date_str = datetime.now().strftime("%Y-%m-%d")
        base_name = os.path.splitext(filename)[0]
        md_filename = f"Оцифровка - {date_str} - {base_name}.md"
        md_path = os.path.join(INBOX_DIR, md_filename)
        
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(response.text)
            
        print(f"[+] Успешно! Markdown-отчет сохранен по пути: {md_path}")
        
        # Cleanup file from Gemini API (good practice)
        genai.delete_file(uploaded_file.name)
        
        # Move audio to archive folder
        dest_path = os.path.join(ARCHIVE_DIR, filename)
        shutil.move(file_path, dest_path)
        print(f"[+] Аудиофайл перемещен в архив: {dest_path}")
        
    except Exception as e:
        print(f"[❌] Ошибка при обработке {filename}: {str(e)}")

def main():
    print("=== Запуск оцифровщика встреч ===")
    print(f"Сканирование папки входящих: {INBOX_DIR}")
    
    audio_files = find_audio_files()
    if not audio_files:
        print("Новых аудиофайлов во входящих не найдено.")
        print(f"Положи аудиозапись (mp3, wav, m4a) в папку {INBOX_DIR} и перезапусти скрипт.")
        return
        
    print(f"Найдено файлов для обработки: {len(audio_files)}")
    for f in audio_files:
        summarize_audio(f)
        
    print("\n=== Обработка завершена ===")

if __name__ == "__main__":
    main()
