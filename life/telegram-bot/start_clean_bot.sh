#!/bin/bash

# 🚀 Чистый запуск Telegram бота без конфликтов
cd "/Users/anton_tsoy/Desktop/Обсидиан/life/telegram-bot"

echo "🔧 Останавливаю все процессы бота..."
pkill -f "python3.*bot.py" 2>/dev/null || true
sleep 2

echo "🧹 Проверяю, что все процессы остановлены..."
if pgrep -f "python3.*bot.py" > /dev/null; then
    echo "⚠️  Некоторые процессы все еще работают, принудительная остановка..."
    pkill -9 -f "python3.*bot.py" 2>/dev/null || true
    sleep 2
fi

echo "🚀 Запускаю чистый экземпляр бота..."
nohup python3 bot.py > bot_clean.log 2>&1 &
BOT_PID=$!

echo "✅ Бот запущен с PID: $BOT_PID"
echo "📋 Логи сохраняются в файл: bot_clean.log"
echo ""
echo "🔍 Проверка статуса..."
sleep 3

if kill -0 $BOT_PID 2>/dev/null; then
    echo "✅ Бот успешно запущен и работает"
    echo ""
    echo "📱 Для тестирования:"
    echo "1. Откройте Telegram"
    echo "2. Найдите бота: @Sreda_academy_bot"
    echo "3. Отправьте: /start"
    echo "4. Нажмите: 🎓 Открыть курс в Web App"
    echo ""
    echo "📊 Команды бота:"
    echo "  /start - Главное меню"
    echo "  /monitor - Мониторинг студентов"
    echo ""
    echo "📄 Для просмотра логов:"
    echo "  tail -f bot_clean.log"
else
    echo "❌ Ошибка: бот не запущен"
    echo "📄 Проверьте логи: cat bot_clean.log"
fi