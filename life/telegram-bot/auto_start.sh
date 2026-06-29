#!/bin/bash

# 🚀 Полная автоматизация запуска Telegram Web App
# Агент берет все под контроль

echo "🚀 Автоматическая настройка Telegram Web App"
echo "==========================================="

cd "/Users/anton_tsoy/Desktop/Обсидиан/life/telegram-bot"

# Стандартный URL для Netlify (имя репозитория + netlify.app)
NETLIFY_URL="https://botsreda.netlify.app"

echo "🔧 Обновляю URL в боте: $NETLIFY_URL"

# Заменяем URL во всех местах в bot.py
sed -i '' "s|https://your-web-app-url.com|$NETLIFY_URL|g" bot.py

echo "✅ URL обновлен в боте"
echo ""
echo "🚀 Запускаю Telegram бота..."

# Проверяем наличие токена
if [ ! -f ".env" ]; then
    echo "⚠️  Файл .env не найден"
    echo "📝 Создаю шаблон .env файла..."
    echo "BOT_TOKEN=YOUR_BOT_TOKEN_HERE" > .env
    echo "GEMINI_API_KEY=YOUR_GEMINI_API_KEY_HERE" >> .env
    echo "❗ Вставьте реальные токены в файл .env и запустите снова"
    exit 1
fi

# Запускаем бота
python3 bot.py