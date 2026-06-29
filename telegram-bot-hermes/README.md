# Бот Hermes: Интеграция Telegram ➔ GitHub ➔ Obsidian

Этот бот слушает ваши сообщения в Telegram (текст и голос), автоматически переводит голос в текст с помощью Gemini API и сохраняет новые файлы заметок непосредственно в ваш GitHub-репозиторий Obsidian.

## Установка и запуск на сервере (VPS)

### 1. Перенос файлов на сервер
Скопируйте директорию `telegram-bot-hermes` на ваш сервер в удобное место (например, `/home/user/telegram-bot-hermes`).

### 2. Настройка окружения
В папке бота на сервере создайте файл `.env`:
```bash
cp .env.example .env
nano .env
```

Заполните переменные:
*   `BOT_TOKEN`: Укажите токен вашего бота (`8663409176:AAGz3f8Ol6YH_PymUuy7sLbPNcfqKsTf4XM`).
*   `ADMIN_IDS`: Ваш численный Telegram ID (можно узнать у бота `@userinfobot` или `@myidbot`). Нужен для защиты, чтобы никто другой не спамил в ваш Obsidian.
*   `GEMINI_API_KEY`: Ваш API-ключ Gemini (для бесплатной и качественной транскрибации голоса в текст).
*   `GITHUB_TOKEN`: Ваш Personal Access Token от GitHub с доступом к репозиторию (в правах токена должно быть выбрано `repo` или доступ к контенту репозиториев `contents:write`).
*   `OBSIDIAN_INBOX_DIR`: Имя папки в репозитории Obsidian, куда будут складываться файлы (по умолчанию `Inbox`).

### 3. Установка зависимостей
Рекомендуется использовать виртуальное окружение Python:
```bash
cd /home/user/telegram-bot-hermes
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 4. Настройка автозапуска (systemd)
Чтобы бот работал 24/7 в фоновом режиме и автоматически перезапускался при сбоях, создайте системную службу.

Создайте файл службы:
```bash
sudo nano /etc/systemd/system/hermes-bot.service
```

Вставьте следующее содержимое (замените пути и пользователя на ваши реальные данные):
```ini
[Unit]
Description=Telegram Hermes Obsidian Bot
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/home/user/telegram-bot-hermes
ExecStart=/home/user/telegram-bot-hermes/venv/bin/python bot.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Активируйте и запустите службу:
```bash
# Перезагрузка демона systemd
sudo systemctl daemon-reload

# Включение автозапуска службы при старте сервера
sudo systemctl enable hermes-bot.service

# Запуск бота прямо сейчас
sudo systemctl start hermes-bot.service

# Проверка статуса бота
sudo systemctl status hermes-bot.service
```

Посмотреть логи бота в реальном времени можно командой:
```bash
sudo journalctl -u hermes-bot.service -f
```
