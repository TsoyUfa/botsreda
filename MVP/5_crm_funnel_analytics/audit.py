import os
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
import google.generativeai as genai

# Load env variables
load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

VAULT_PATH = os.getenv("OBSIDIAN_VAULT_PATH", "/Users/anton_tsoy/Desktop/Обсидиан")
WORKING_DIR = os.path.dirname(__file__)
CSV_PATH = os.path.join(WORKING_DIR, "deals.csv")
OUTPUT_DIR = os.path.join(VAULT_PATH, "inbox")

# Configure Gemini
api_key = os.getenv("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)
else:
    print("Warning: GEMINI_API_KEY is not set.")

def create_mock_csv():
    """Generates a realistic mock deals.csv file if it doesn't exist."""
    print("[~] deals.csv не найден. Генерация демонстрационного файла сделок...")
    
    mock_data = [
        {"ID": 1001, "Title": "ЖК Центральный, 2кк", "Stage": "Сделка закрыта", "Broker": "Дмитрий", "SLA_Delay_Min": 15, "Last_Comment": "Сделка оформлена. Субсидия 3% подошла идеально."},
        {"ID": 1002, "Title": "ЖК Символ, 1кк", "Stage": "Отказ", "Broker": "Елена", "SLA_Delay_Min": 120, "Last_Comment": "Клиент ушел. Сказал, что ставки высокие и лучше будет арендовать. Не отработала возражение."},
        {"ID": 1003, "Title": "ЖК Новатор, Студия", "Stage": "Встреча назначена", "Broker": "Сергей", "SLA_Delay_Min": 5, "Last_Comment": "Согласовали встречу на пятницу. Отправил расчет по траншевой ипотеке."},
        {"ID": 1004, "Title": "ЖК Центральный, 1кк", "Stage": "Отказ", "Broker": "Дмитрий", "SLA_Delay_Min": 45, "Last_Comment": "Отказ. Клиент побоялся траншевой схемы, сказал, что застройщик обанкротится."},
        {"ID": 1005, "Title": "ЖК Символ, 3кк", "Stage": "Экскурсия", "Broker": "Елена", "SLA_Delay_Min": 90, "Last_Comment": "Едем на показ во вторник. Клиент хочет увидеть планировку вживую."},
        {"ID": 1006, "Title": "ЖК Новатор, 2кк", "Stage": "Квалифицирована", "Broker": "Сергей", "SLA_Delay_Min": 180, "Last_Comment": "Выявил потребность, клиент выбирает между ЖК. Долго не перезванивал."},
        {"ID": 1007, "Title": "ЖК Центральный, Студия", "Stage": "Сделка закрыта", "Broker": "Дмитрий", "SLA_Delay_Min": 10, "Last_Comment": "Сделка закрыта. Оформили транш на 10 месяцев."},
        {"ID": 1008, "Title": "ЖК Символ, 2кк", "Stage": "Отказ", "Broker": "Елена", "SLA_Delay_Min": 240, "Last_Comment": "Не дозвонилась, сделка в отказе. SLA нарушен жестко."},
        {"ID": 1009, "Title": "ЖК Новатор, 3кк", "Stage": "Новая", "Broker": "Сергей", "SLA_Delay_Min": 10, "Last_Comment": "Новый лид с Reels по кодовому слову. Отправил лид-магнит."},
        {"ID": 1010, "Title": "ЖК Гранд, 1кк", "Stage": "Квалифицирована", "Broker": "Сергей", "SLA_Delay_Min": 60, "Last_Comment": "Клиент думает. Говорит, что новостройки переоценены, инвестор."}
    ]
    
    df = pd.DataFrame(mock_data)
    df.to_csv(CSV_PATH, index=False, encoding='utf-8')
    print(f"[+] Демонстрационный файл успешно создан: {CSV_PATH}")

def run_analytics():
    if not os.path.exists(CSV_PATH):
        create_mock_csv()
        
    print(f"[~] Чтение файла сделок: {CSV_PATH}")
    try:
        df = pd.read_csv(CSV_PATH, encoding='utf-8')
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return
        
    print("[~] Анализ воронки продаж...")
    
    # 1. Pipeline Stage counts
    stage_counts = df["Stage"].value_counts().to_dict()
    
    # 2. Broker SLA delays
    broker_sla = df.groupby("Broker")["SLA_Delay_Min"].mean().round(1).to_dict()
    
    # 3. Lost deals comments
    lost_deals = df[df["Stage"] == "Отказ"]
    lost_list = []
    for _, row in lost_deals.iterrows():
        lost_list.append({
            "ID": row["ID"],
            "Broker": row["Broker"],
            "Title": row["Title"],
            "Comment": row["Last_Comment"]
        })
        
    # Calculate simple ratios
    total_deals = len(df)
    closed_won = len(df[df["Stage"] == "Сделка закрыта"])
    lost_count = len(lost_deals)
    in_progress = total_deals - closed_won - lost_count
    
    won_rate = (closed_won / total_deals) * 100 if total_deals > 0 else 0
    lost_rate = (lost_count / total_deals) * 100 if total_deals > 0 else 0
    
    # Format metrics summary for Gemini
    summary_data = {
        "total_deals": total_deals,
        "won_count": closed_won,
        "lost_count": lost_count,
        "in_progress_count": in_progress,
        "won_rate_percent": round(won_rate, 1),
        "lost_rate_percent": round(lost_rate, 1),
        "stage_distribution": stage_counts,
        "broker_average_sla_delay_min": broker_sla,
        "lost_deals_details": lost_list
    }
    
    print("[~] ИИ анализирует выгрузку CRM...")
    
    prompt = f"""
Ты — высококлассный CRM-аналитик и аудитор отделов продаж в сфере недвижимости.
Твоя задача — проанализировать агрегированный отчет по сделкам и составить подробную диагностическую записку в формате Markdown.

Вот статистические данные выгрузки:
{json.dumps(summary_data, ensure_ascii=False, indent=2)}

Напиши аудит со следующей структурой:

# 📊 Аудит воронки продаж и дисциплины CRM

* **Дата аудита:** {datetime.now().strftime("%Y-%m-%d")}
* **Проанализировано сделок:** {total_deals} шт.

---

## 📈 Метрики эффективности воронки
* **Конверсия в закрытые сделки (Won Rate):** {round(won_rate, 1)}%
* **Доля отказов (Lost Rate):** {round(lost_rate, 1)}%
* **Распределение сделок по этапам:**
[Нарисуй небольшую текстовую схему или таблицу распределения]

---

## 🕒 SLA и Скорость ответа (Дисциплина)
* **Среднее время задержки ответа (SLA) по брокерам:**
  [Выведи список брокеров и их среднее время ответа. Укажи, кто нарушает стандарты (стандарт — ответ в течение 15 минут)]

---

## 🔍 Глубокий разбор проигранных сделок (Отказов)
Проанализируй комментарии по потерянным сделкам:
{json.dumps(lost_list, ensure_ascii=False, indent=2)}

Укажи:
1. **Каковы основные причины отказов клиентов?** (например, испугались траншевой схемы, испугались высоких ставок).
2. **Ошибки брокеров:** Где брокер не отработал возражение? Где сделка слита из-за задержки ответа (SLA)?

---

## 🛠️ План корректирующих действий (Рекомендации Антона Цоя)
Дай 3-4 конкретные практические рекомендации для руководителя отдела продаж (что исправить в скриптах, кого наказать за дисциплину, какие памятки раздать брокерам).

Ответ верни на русском языке в чистой разметке Markdown.
"""

    if not api_key:
        mock_audit = f"""# 📊 Имитация Аудита CRM (API Ключ не задан)
* Всего сделок: {total_deals}
* Успешных сделок: {closed_won}
* Потерянных сделок: {lost_count}
* Средний SLA по брокерам: {broker_sla}
* Рекомендация: Пропишите регламент отправки расчетов траншей в первые 15 минут.
"""
        save_report(mock_audit)
        return

    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        save_report(response.text)
    except Exception as e:
        print(f"[❌] Ошибка Gemini API: {e}")

def save_report(report_text):
    date_str = datetime.now().strftime("%Y-%m-%d")
    report_filename = f"Анализ воронки CRM - {date_str}.md"
    report_path = os.path.join(OUTPUT_DIR, report_filename)
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report_text)
        
    print(f"[+] Аудит воронки успешно сгенерирован: {report_path}")
    print("Вы можете открыть этот файл прямо в Obsidian.")

if __name__ == "__main__":
    run_analytics()
