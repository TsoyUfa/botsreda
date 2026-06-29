#!/bin/bash
# Скрипт публикации Obsidian vault + Dashboard на GitHub
# Использование: ./publish_to_github.sh [сообщение коммита]

set -e

cd "/Users/anton_tsoy/Desktop/Обсидиан" || {
  echo "❌ Не удалось перейти в директорию Obsidian"
  exit 1
}

echo "🎯 Обновление дашборда из Obsidian vault..."

# Генерируем свежие данные для дашборда
if command -v python3 &>/dev/null; then
  python3 dashboard/generate_data.py && echo "✅ data.json обновлён"
else
  echo "⚠️  Python3 не найден — data.json не обновлён"
fi

echo ""
echo "📝 Добавляем файлы в git..."
git add -A

echo "📊 Статус:"
git status --short

# Сообщение коммита
COMMIT_MSG="${1:-🔄 Vault sync $(date '+%d.%m.%Y %H:%M')}"

echo ""
echo "✍️  Коммит: $COMMIT_MSG"
git commit -m "$COMMIT_MSG" || echo "⚠️  Нет изменений для коммита"

echo ""
echo "🚀 Публикация на GitHub..."
git push origin main

echo ""
echo "✅ Готово!"
echo "🔗 Vault:      https://github.com/TsoyUfa/obsidian-vault"
echo "🎯 Dashboard:  https://TsoyUfa.github.io/obsidian-vault/dashboard/"