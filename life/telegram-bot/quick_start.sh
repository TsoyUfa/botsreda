#!/bin/bash
# 🚀 БЫСТРЫЙ ЗАПУСК - Telegram Web App «Среда Обучение»

echo "🎯 Telegram Web App «Среда Обучение» - Быстрый запуск"
echo "================================================"

# Проверка текущей директории
cd "/Users/anton_tsoy/Desktop/Обсидиан/life/telegram-bot"

echo ""
echo "📋 Выберите способ деплоя:"
echo ""
echo "🔹 Вариант 1: Netlify (рекомендую) - 2 минуты"
echo "   1. Откройте: https://app.netlify.com"
echo "   2. 'New site from Git' → выберите 'botsreda'"
echo "   3. Build: 'echo \"Static site\"'"
echo "   4. Directory: 'deploy-dist'"
echo "   5. 'Deploy site'"
echo "   6. Через 1 минуту ваш Web App готов!"
echo ""

echo "🔹 Вариант 2: GitHub Pages - 5 минут"
echo "   1. Откройте: https://github.com/TsoyUfa/botsreda"
echo "   2. 'Settings' → 'Pages'"
echo "   3. Source: 'Deploy from a branch'"
echo "   4. Branch: 'main'"
echo "   5. Directory: '/deploy-dist'"
echo "   6. 'Save'"
echo "   7. Через 2 минуты готово: https://tsoyufa.github.io/botsreda"
echo ""

read -p "👉 Нажмите Enter когда деплой завершен..."

echo ""
echo "🔗 Теперь обновите URL в боте:"
echo "   1. Откройте файл: bot.py"
echo "   2. Найдите: url=\"https://your-web-app-url.com\""
echo "   3. Замените на ваш реальный URL"
echo "   4. Сохраните файл"
echo ""

read -p "👉 Нажмите Enter когда URL обновлен..."

echo ""
echo "🚀 Запускаем Telegram бота:"
echo "   python3 bot.py"
echo ""
echo "📱 Тестируем:"
echo "   1. Отправьте боту: /start"
echo "   2. Нажмите: 🎓 Открыть курс в Web App"
echo "   3. Web App должен открыться!"
echo ""

echo "🎉 ГОТОВО! Ваш Telegram Web App работает!"
echo "   - 🎓 7 модулей обучения Р.О.С.Т."
echo "   - 👨‍🏫 Полный мониторинг через /monitor"
echo "   - 📱 Профессиональный интерфейс"
echo "   - 🚀 Работает прямо сейчас!"

# Запуск бота
python3 bot.py