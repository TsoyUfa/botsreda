#!/bin/bash

# 🚀 Автоматический скрипт деплоя Telegram Web App
# Создан агентом для полного автопилота

echo "🚀 Запускаю автоматический деплой Web App..."
echo "====="

# Проверка текущего состояния
echo "📋 Проверка статуса Git..."
cd "/Users/anton_tsoy/Desktop/Обсидиан/life/telegram-bot"

# Проверка, есть ли коммиты для пуша
if git log --oneline origin/main..main | grep -q "."; then
    echo "⏳ Есть непушеные коммиты, отправляю..."
    git push origin main
    echo "✅ Коммиты отправлены на GitHub"
else
    echo "✅ Все коммиты уже на GitHub"
fi

echo ""
echo "🌐 Выберите способ деплоя:"
echo "1) GitHub Pages (просто, бесплатно)"
echo "2) Netlify (красивее, рекомендуется)"
echo ""
read -p "Введите номер (1 или 2): " choice

case $choice in
    1)
        echo "🔧 Настраиваю GitHub Pages..."
        echo ""
        echo "📋 Инструкция:"
        echo "1. Откройте: https://github.com/TsoyUfa/botsreda"
        echo "2. Нажмите 'Settings' → 'Pages'"
        echo "3. Source: 'Deploy from a branch'"
        echo "4. Branch: 'main'"
        echo "5. Directory: '/deploy-dist'"
        echo "6. Нажмите 'Save'"
        echo ""
        echo "⏳ Через 1-2 минуты сайт будет доступен по адресу:"
        echo "   https://tsoyufa.github.io/botsreda"
        ;;
    2)
        echo "🚀 Настраиваю Netlify..."
        echo ""
        echo "📋 Инструкция:"
        echo "1. Откройте: https://app.netlify.com"
        echo "2. 'New site from Git'"
        echo "3. Выберите репозиторий 'botsreda'"
        echo "4. Настройки сборки:"
        echo "   - Build command: echo 'Static site'"
        echo "   - Publish directory: deploy-dist"
        echo "5. Нажмите 'Deploy site'"
        echo ""
        echo "⏳ Через 1 минуту сайт будет доступен по красивому URL"
        ;;
    *)
        echo "❌ Неверный выбор"
        exit 1
        ;;
esac

echo ""
echo "🔗 После деплоя:"
echo "1. Скопируйте URL вашего сайта"
echo "2. Откройте файл: bot.py"
echo "3. Найдите строку: url=\"https://your-web-app-url.com\""
echo "4. Замените на ваш реальный URL"
echo "5. Запустите бота: python3 bot.py"
echo "6. Тест: /start → 🎓 Открыть курс в Web App"

echo ""
echo "🎉 Готово! Ваш Telegram Web App будет работать через 10 минут!"
echo "====="