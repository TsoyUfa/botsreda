#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для быстрой структуризации заметок по квадрантам РОСТ
Анализирует входящий текст и определяет, в какой квадрант его поместить
"""

import os
import re
import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple

class NotesStructurer:
    """Класс для автоматической структуризации заметок"""
    
    def __init__(self, vault_path: str = "/Users/anton_tsoy/Desktop/Обсидиан"):
        self.vault_path = vault_path
        self.quadrants = {
            "business": "1. Бизнес",
            "plan": "2. План", 
            "clone": "3. Мой клон",
            "mastery": "4. Мастерство"
        }
        
        # Ключевые слова для определения типа контента
        self.keywords = {
            "business": [
                "деньги", "цена", "стоимость", "доход", "выручка", "прибыль",
                "клиент", "заказчик", "покупатель", "партнер", "застройщик",
                "продаж", "продать", "оффер", "предложение", "тариф",
                "сделка", "договор", "контракт", "соглашение",
                "выставка", "конференция", "встреча", "переговоры",
                "рынок", "конкуренция", "ниша", "сегмент"
            ],
            "plan": [
                "задача", "план", "проект", "цель", "дедлайн", "срок",
                "этап", "фаза", "шаг", "действие", "мероприятие",
                "завершить", "сделать", "реализовать", "выполнить",
                "roadmap", "карта", "график", "расписание",
                "приоритет", "важно", "срочно", "блокер"
            ],
            "clone": [
                "я", "мой", "меня", "мной", "личный", "лично",
                "стиль", "голос", "тон", "манера", "подача",
                "принцип", "ценность", "убеждение", "верую",
                "характер", "темперамент", "поведение", "привычка",
                "бренд", "имидж", "репутация", "образ"
            ],
            "mastery": [
                "метод", "методика", "фреймворк", "подход", "система",
                "эксперт", "профессионал", "мастер", "специалист",
                "практика", "опыт", "навык", "умение", "компетенция",
                "шаблон", "template", "чекаут", "инструкция", "регламент",
                "стандарт", "качество", "оптимизация", "эффективность"
            ]
        }
        
        # Подпапки для каждого квадранта
        self.subfolders = {
            "business": [
                "01_strategy", "02_offers", "03_audiences", "04_sales",
                "05_finance", "06_cases", "07_network", "08_ai_crm_stack", "09_operations"
            ],
            "plan": [
                "01_launch_ai_entrepreneurs", "02_clients", "conclusions"
            ],
            "clone": [
                "identity", "voice", "thinking", "principles", 
                "style", "feedback", "reference", "interview"
            ],
            "mastery": [
                "sales", "negotiations", "copywriting", "product",
                "financial-analysis", "real-estate-developers", "ai-automation", "decision-making"
            ]
        }
    
    def analyze_content(self, text: str) -> Tuple[str, float]:
        """
        Анализирует текст и определяет тип контента
        
        Returns:
            Tuple[str, float]: (тип контента, уверенность)
        """
        text_lower = text.lower()
        scores = {}
        
        for content_type, keywords in self.keywords.items():
            score = 0
            for keyword in keywords:
                # Подсчет вхождений ключевых слов
                matches = len(re.findall(rf'\b{re.escape(keyword)}\b', text_lower))
                score += matches
            
            # Нормализация счета
            scores[content_type] = score
        
        # Определение типа с максимальным счетом
        if max(scores.values()) == 0:
            return "general", 0.0
        
        best_type = max(scores, key=scores.get)
        total_score = sum(scores.values())
        confidence = scores[best_type] / total_score if total_score > 0 else 0.0
        
        return best_type, confidence
    
    def determine_subfolder(self, text: str, content_type: str) -> str:
        """
        Определяет подходящую подпапку для заметки
        """
        if content_type == "general":
            return "raw"
        
        subfolder_keywords = {
            "business": {
                "01_strategy": ["стратегия", "фильтр", "фокус", "направление", "приоритет"],
                "02_offers": ["оффер", "продукт", "услуга", "тариф", "пакет"],
                "03_audiences": ["аудитория", "клиент", "покупатель", "сегмент", "портрет"],
                "04_sales": ["продажа", "скрипт", "воронка", "возражение", "презентация"],
                "05_finance": ["деньги", "цена", "финансы", "экономика", "доход"],
                "06_cases": ["кейс", "проект", "история", "результат", "пример"],
                "07_network": ["партнер", "связь", "контакт", "знакомство", "сотрудничество"],
                "08_ai_crm_stack": ["ai", "crm", "автоматизация", "технология", "система"],
                "09_operations": ["операция", "процесс", "доставка", "регламент", "sl"]
            },
            "plan": {
                "01_launch_ai_entrepreneurs": ["запуск", "ai", "предприниматель", "стартап"],
                "02_clients": ["клиент", "проект", "задача", "crm"],
                "conclusions": ["вывод", "итог", "заключение", "результат"]
            },
            "clone": {
                "identity": ["личность", "биография", "миссия", "видение", "ценность"],
                "voice": ["голос", "тон", "стиль", "словарь", "фразы"],
                "thinking": ["мышление", "модель", "подход", "логика"],
                "principles": ["принцип", "правило", "убеждение", "стандарт"],
                "style": ["стиль", "формат", "подача", "структура"],
                "feedback": ["обратная связь", "корректировка", "правка"],
                "reference": ["справка", "инструмент", "система", "ограничение"],
                "interview": ["вопрос", "интервью", "анкета"]
            },
            "mastery": {
                "sales": ["продажа", "скрипт", "метод", "техника"],
                "negotiations": ["переговоры", "договор", "соглашение"],
                "copywriting": ["текст", "копирайтинг", "письмо", "контент"],
                "product": ["продукт", "mvp", "упаковка", "создание"],
                "financial-analysis": ["финансы", "анализ", "roi", "экономика"],
                "real-estate-developers": ["застройщик", "недвижимость", "жк"],
                "ai-automation": ["ai", "автоматизация", "бот", "система"],
                "decision-making": ["решение", "выбор", "анализ", "оценка"]
            }
        }
        
        text_lower = text.lower()
        best_subfolder = "raw"
        best_score = 0
        
        if content_type in subfolder_keywords:
            for subfolder, keywords in subfolder_keywords[content_type].items():
                score = 0
                for keyword in keywords:
                    matches = len(re.findall(rf'\b{re.escape(keyword)}\b', text_lower))
                    score += matches
                
                if score > best_score:
                    best_score = score
                    best_subfolder = subfolder
        
        return best_subfolder
    
    def generate_filename(self, title: str, content_type: str) -> str:
        """
        Генерирует имя файла для заметки
        """
        # Очищаем заголовок от недопустимых символов
        clean_title = re.sub(r'[^\w\s-]', '', title)
        clean_title = re.sub(r'\s+', '-', clean_title)
        
        # Добавляем дату и тип
        date_str = datetime.now().strftime("%Y-%m-%d")
        filename = f"{date_str}_{content_type}_{clean_title.lower()}.md"
        
        # Ограничиваем длину
        if len(filename) > 100:
            filename = filename[:97] + "..."
        
        return filename
    
    def create_note(self, title: str, content: str, content_type: str = "auto") -> str:
        """
        Создает заметку в соответствующей папке
        
        Returns:
            str: путь к созданному файлу
        """
        if content_type == "auto":
            content_type, confidence = self.analyze_content(content)
            print(f"Определен тип контента: {content_type} (уверенность: {confidence:.2f})")
        
        # Определяем подпапку
        subfolder = self.determine_subfolder(content, content_type)
        
        # Создаем путь
        folder_path = os.path.join(self.vault_path, self.quadrants[content_type], subfolder)
        os.makedirs(folder_path, exist_ok=True)
        
        # Генерируем имя файла
        filename = self.generate_filename(title, content_type)
        file_path = os.path.join(folder_path, filename)
        
        # Находим связанные заметки
        related_notes = self.find_related_notes(content)
        
        # Создаем содержимое файла
        note_content = self.format_note(title, content, content_type, subfolder, related_notes)
        
        # Записываем файл
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(note_content)
        
        print(f"Заметка создана: {file_path}")
        return file_path
    
    def find_related_notes(self, content: str) -> List[str]:
        """
        Находит связанные заметки в vault
        """
        # Здесь можно реализовать поиск по содержимому vault
        # Для примера возвращаем пустой список
        return []
    
    def format_note(self, title: str, content: str, content_type: str, 
                   subfolder: str, related_notes: List[str]) -> str:
        """
        Форматирует содержимое заметки
        """
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        note_template = f"""# {title}

**Тип:** {content_type}  
**Подкатегория:** {subfolder}  
**Дата создания:** {current_time}  

## Содержание
{content}

"""

        if related_notes:
            note_template += "## Связанные заметки\n"
            for note in related_notes:
                note_template += f"- [[{note}]]\n"
            note_template += "\n"
        
        note_template += f"""---
*Автоматически создано системой структуризации заметок*
*Тип контента: {content_type}*
*Квадрант: {self.quadrants[content_type]}*
"""
        
        return note_template
    
    def process_input(self, text: str, title: str = None) -> str:
        """
        Обрабатывает входной текст и создает заметку
        """
        if not title:
            # Извлекаем заголовок из первого предложения
            first_sentence = text.split('.')[0]
            title = first_sentence[:50] + ('...' if len(first_sentence) > 50 else '')
        
        return self.create_note(title, text)

def main():
    """Основная функция для командной строки"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Структуризация заметок по квадрантам РОСТ")
    parser.add_argument("text", help="Текст заметки")
    parser.add_argument("--title", "-t", help="Заголовок заметки")
    parser.add_argument("--type", "-y", choices=["business", "plan", "clone", "mastery", "auto"],
                       default="auto", help="Тип контента")
    
    args = parser.parse_args()
    
    structurer = NotesStructurer()
    file_path = structurer.create_note(args.title or "Без названия", args.text, args.type)
    
    print(f"Заметка создана: {file_path}")

if __name__ == "__main__":
    main()