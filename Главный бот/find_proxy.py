import os
import re
import sys
import urllib.request
import concurrent.futures

# URL списков бесплатных HTTP-прокси
PROXY_SOURCES = [
    "https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/http.txt",
    "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt",
    "https://raw.githubusercontent.com/clket/proxy-list/master/http.txt"
]

def get_bot_token():
    """Чтение BOT_TOKEN из файла .env."""
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip().startswith("BOT_TOKEN="):
                    return line.strip().split("=", 1)[1]
    return None

def fetch_proxies():
    """Скачивание списков прокси из внешних репозиториев."""
    proxies = set()
    print("📥 Скачивание списков публичных HTTP-прокси...")
    
    headers = {"User-Agent": "Mozilla/5.0"}
    for url in PROXY_SOURCES:
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=8) as response:
                content = response.read().decode('utf-8')
                # Извлекаем все строки вида ip:port
                found = re.findall(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d{2,5}\b", content)
                proxies.update(found)
        except Exception as e:
            print(f"⚠️ Не удалось загрузить прокси с {url}: {e}")
            
    print(f"🎯 Всего загружено прокси для проверки: {len(proxies)}")
    return list(proxies)

def test_single_proxy(proxy_ip_port, token):
    """Проверка одного прокси-сервера на доступность к Telegram Bot API."""
    proxy_url = f"http://{proxy_ip_port}"
    try:
        # Настройка прокси для urllib
        proxy_handler = urllib.request.ProxyHandler({'http': proxy_url, 'https': proxy_url})
        opener = urllib.request.build_opener(proxy_handler)
        
        # Запрос к Telegram Bot API
        url = f"https://api.telegram.org/bot{token}/getMe"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        
        with opener.open(req, timeout=3.0) as response:
            if response.status == 200:
                return proxy_url
    except Exception:
        pass
    return None

def save_proxy_to_env(proxy_url):
    """Запись PROXY_URL в файл .env."""
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    lines = []
    proxy_written = False
    
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip().startswith("PROXY_URL="):
                    lines.append(f"PROXY_URL={proxy_url}\n")
                    proxy_written = True
                else:
                    lines.append(line)
                    
    if not proxy_written:
        # Добавляем в конец файла
        if lines and not lines[-1].endswith("\n"):
            lines.append("\n")
        lines.append(f"PROXY_URL={proxy_url}\n")
        
    with open(env_path, "w", encoding="utf-8") as f:
        f.writelines(lines)
    print(f"💾 Прокси сохранен в .env: {proxy_url}")

def main():
    token = get_bot_token()
    if not token or token == "your_telegram_bot_token_here":
        print("❌ Ошибка: В файле .env не задан BOT_TOKEN!")
        sys.exit(1)
        
    proxies = fetch_proxies()
    if not proxies:
        print("❌ Ошибка: Не удалось получить списки прокси!")
        sys.exit(1)
        
    print("⏳ Тестирование прокси-серверов в 40 потоков... Ожидайте.")
    working_proxy = None
    
    # Запуск параллельной проверки
    with concurrent.futures.ThreadPoolExecutor(max_workers=40) as executor:
        futures = {executor.submit(test_single_proxy, p, token): p for p in proxies}
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            if result:
                working_proxy = result
                # Как только найден первый рабочий прокси, останавливаем проверку остальных
                print(f"🔥 Найден рабочий прокси: {working_proxy}")
                break
                
    if working_proxy:
        save_proxy_to_env(working_proxy)
        print("🎉 Процесс завершен успешно!")
    else:
        print("❌ К сожалению, ни один из прокси не прошел проверку. Попробуйте запустить позже.")
        sys.exit(1)

if __name__ == "__main__":
    main()
