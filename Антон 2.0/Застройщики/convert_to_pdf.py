#!/usr/bin/env python3
"""
Скрипт для конвертации HTML-презентации в PDF
Требуется: pip install playwright
После установки: playwright install chromium
"""

import os
import sys
from pathlib import Path

def convert_html_to_pdf():
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("❌ Ошибка: playwright не установлен")
        print("Установите его командой: pip install playwright")
        print("Затем установите браузер: playwright install chromium")
        sys.exit(1)
    
    # Пути к файлам
    script_dir = Path(__file__).parent
    html_file = script_dir / "Коммерческое предложение - Аудит потенциала продаж - Презентация.html"
    pdf_file = script_dir / "Коммерческое предложение - Аудит потенциала продаж - Презентация.pdf"
    
    if not html_file.exists():
        print(f"❌ Файл не найден: {html_file}")
        sys.exit(1)
    
    print(f"📄 Конвертирую: {html_file.name}")
    print("⏳ Пожалуйста, подождите...")
    
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        
        # Открываем HTML файл
        page.goto(f"file://{html_file.absolute()}")
        
        # Ждем загрузки
        page.wait_for_load_state("networkidle")
        
        # Сохраняем в PDF с настройками для презентации
        page.pdf(
            path=str(pdf_file),
            format="A4",
            landscape=True,
            print_background=True,
            margin={
                "top": "0",
                "right": "0",
                "bottom": "0",
                "left": "0"
            }
        )
        
        browser.close()
    
    print(f"✅ PDF создан: {pdf_file.name}")
    print(f"📁 Путь: {pdf_file.absolute()}")

if __name__ == "__main__":
    convert_html_to_pdf()


