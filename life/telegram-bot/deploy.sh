#!/bin/bash

# Скрипт для подготовки и выгрузки Web App на хостинг
# Поддерживаемые платформы: Netlify, Vercel, GitHub Pages

echo "🚀 Подготовка Telegram Web App к выгрузке на хостинг..."
echo "================================================"

# Проверка необходимых файлов
if [ ! -d "webapp" ]; then
    echo "❌ Ошибка: директория webapp не найдена!"
    exit 1
fi

# Создаем временную директорию для деплоя
DEPLOY_DIR="deploy-dist"
rm -rf $DEPLOY_DIR
mkdir -p $DEPLOY_DIR

# Копируем Web App файлы
echo "📁 Копирование файлов Web App..."
cp -r webapp/* $DEPLOY_DIR/

# Создаем файл с конфигурацией для деплоя
cat > $DEPLOY_DIR/_config.yml << EOF
title: "Среда Обучение - Telegram Web App"
description: "Полноценная система обучения внутри Telegram"
author: "Anton Tsoy"
version: "1.0.0"
telegram_bot: "@Sreda_academy_bot"
EOF

# Создаем index.html с указанием на удаленный API (если нужно)
echo "📝 Обновление конфигурации для продакшена..."

# Копируем конфиги хостинга
if [ -f "netlify.toml" ]; then
    cp netlify.toml $DEPLOY_DIR/
    echo "✅ Netlify конфиг скопирован"
fi

if [ -f "vercel.json" ]; then
    cp vercel.json $DEPLOY_DIR/
    echo "✅ Vercel конфиг скопирован"
fi

# Создаем файл CNAME для кастомного домена (если нужен)
cat > $DEPLOY_DIR/CNAME << EOF
your-domain.com
EOF

echo ""
echo "✅ Подготовка завершена!"
echo "📦 Готово к выгрузке на хостинг"
echo ""
echo "🎯 Следующие шаги:"
echo ""

# Проверка наличия git
if git rev-parse --git-dir > /dev/null 2>&1; then
    echo "📋 1. Зафиксируйте изменения в Git:"
    echo "   git add ."
    echo "   git commit -m 'Deploy Telegram Web App v1.0'"
    echo ""
    
    echo "🚀 2. Выберите платформу для деплоя:"
    echo ""
    echo "   🔹 Netlify (рекомендуется):"
    echo "   1. Зайдите на https://netlify.com"
    echo "   2. 'New site from Git' -> выберите этот репозиторий"
    echo "   3. Build settings: publish directory = 'deploy-dist'"
    echo "   4. Deploy site"
    echo ""
    echo "   🔹 Vercel:"
    echo "   1. Зайдите на https://vercel.com"
    echo "   2. 'New Project' -> Import Git Repository"
    echo "   3. Выберите этот репозиторий"
    echo "   4. Framework Preset: Other"
    echo "   5. Output Directory: deploy-dist"
    echo "   6. Deploy"
    echo ""
    echo "   🔹 GitHub Pages:"
    echo "   1. В настройках GitHub репозитория"
    echo "   2. Pages -> Source -> Deploy from a branch"
    echo "   3. Branch: main/main/master"
    echo "   4. Directory: /deploy-dist"
    echo "   5. Save"
    echo ""
else
    echo "⚠️  Git не инициализирован. Для авто-деплоя через платформы:"
    echo "   git init"
    echo "   git add ."
    echo "   git commit -m 'Initial commit'"
    echo ""
    echo "Или вручную загрузите папку $DEPLOY_DIR на ваш хостинг"
fi

echo ""
echo "🔧 3. После деплоя:"
echo "   - Скопируйте URL вашего сайта"
echo "   - Обновите URL в файле bot.py"
echo "   - Перезапустите Telegram бота"
echo ""
echo "📱 4. Тестирование:"
echo "   - Отправьте боту /start"
echo "   - Нажмите кнопку '🎓 Открыть курс в Web App'"
echo "   - Web App должен открыться в Telegram"
echo ""
echo "✅ Всё готово к выгрузке!"