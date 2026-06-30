import os
import sys
import time
import subprocess
from datetime import datetime

WATCH_DIR = os.path.dirname(os.path.abspath(__file__))
OBSIDIAN_DIR = "/Users/anton_tsoy/Desktop/Обсидиан/6. обучения агентов"

def get_last_modified_time():
    max_time = 0
    # Проверяем файлы python и конфигурацию
    for root, dirs, files in os.walk(WATCH_DIR):
        if any(x in root for x in ["data", ".git", "__pycache__", ".venv", ".agents"]):
            continue
        for file in files:
            if file.endswith(".py") or file.endswith(".env"):
                filepath = os.path.join(root, file)
                try:
                    mtime = os.path.getmtime(filepath)
                    if mtime > max_time:
                        max_time = mtime
                except OSError:
                    pass
                    
    # Проверяем файлы Obsidian
    if os.path.exists(OBSIDIAN_DIR):
        for root, dirs, files in os.walk(OBSIDIAN_DIR):
            for file in files:
                if file.endswith(".md"):
                    filepath = os.path.join(root, file)
                    try:
                        mtime = os.path.getmtime(filepath)
                        if mtime > max_time:
                            max_time = mtime
                    except OSError:
                        pass
    return max_time

def main():
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 🔄 Запуск авто-релоадера Среда 2.0...")
    
    bot_process = None
    web_process = None
    last_mtime = get_last_modified_time()
    
    def start_processes():
        nonlocal bot_process, web_process
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 🚀 Запуск bot.py и webapp_server.py...")
        # Запускаем бот и сервер
        bot_process = subprocess.Popen([sys.executable, "bot.py"], cwd=WATCH_DIR)
        web_process = subprocess.Popen([sys.executable, "webapp_server.py"], cwd=WATCH_DIR)
        
    def stop_processes():
        nonlocal bot_process, web_process
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 🛑 Перезагрузка процессов...")
        for proc in [bot_process, web_process]:
            if proc:
                try:
                    proc.terminate()
                    proc.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    proc.kill()
                except Exception:
                    pass
        bot_process = None
        web_process = None
        
    start_processes()
    
    try:
        while True:
            time.sleep(1.0)
            current_mtime = get_last_modified_time()
            if current_mtime > last_mtime:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] ⚡ Обнаружены изменения в файлах!")
                last_mtime = current_mtime
                stop_processes()
                time.sleep(0.5)
                start_processes()
    except KeyboardInterrupt:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 🛑 Выход. Завершаем процессы...")
        stop_processes()

if __name__ == "__main__":
    main()
