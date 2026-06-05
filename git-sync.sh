#!/bin/bash

# Переходим в папку Базы знаний
cd /Users/anton_tsoy/Desktop/Обсидиан

# Загружаем внешние изменения из Гитхаба
git pull origin main --rebase

# Добавляем все локальные изменения
git add -A

# Если есть что коммитить - коммитим и отправляем
if ! git diff-index --quiet HEAD --; then
  git commit -m "Автоматическая фоновая синхронизация Базы знаний"
  git push origin main
fi
