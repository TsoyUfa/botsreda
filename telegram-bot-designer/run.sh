#!/bin/bash

# Определение рабочей директории скрипта
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

PORT=8080

# Поиск свободного порта, если 8080 занят
while lsof -i :$PORT >/dev/null 2>&1; do
  PORT=$((PORT+1))
done

echo "=========================================================="
echo "🤖 Запуск BotSreda Designer на http://localhost:$PORT"
echo "=========================================================="

# Запуск простого HTTP-сервера Python в фоновом режиме
python3 -m http.server $PORT > /dev/null 2>&1 &
SERVER_PID=$!

# Функция для завершения сервера при закрытии скрипта
cleanup() {
  echo ""
  echo "Остановка сервера (PID: $SERVER_PID)..."
  kill $SERVER_PID
  exit 0
}
trap cleanup SIGINT SIGTERM

# Ожидание 1 секунды для запуска сервера
sleep 1

# Открытие страницы в браузере (на macOS используется open)
open "http://localhost:$PORT"

echo "Конструктор ботов успешно запущен!"
echo "Для остановки нажмите Ctrl+C"
echo "=========================================================="

# Ожидание завершения фонового процесса сервера
wait $SERVER_PID
