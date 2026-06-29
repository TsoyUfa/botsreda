# 🤖 Шаблон Telegram-бота для обучения

## Описание шаблона

Готовый шаблон Telegram-бота для создания обучающих платформ. Включает в себя систему модулей, тестирования, платежей и администрирования.

## 🏗️ Структура проекта

```
telegram-bot-obuchenie/
├── config.py              # Конфигурация бота
├── db.py                 # Работа с базой данных
├── bot.py                # Основной файл бота
├── handlers/             # Обработчики команд
│   ├── admin.py         # Административные функции
│   ├── user.py          # Пользовательские функции
│   ├── payment.py       # Обработка платежей
│   └── testing.py       # Система тестирования
├── services/             # Сервисы
│   ├── gemini_service.py # Интеграция с Gemini AI
│   └── payment_service.py # Обработка платежей
├── templates/           # Шаблоны сообщений
├── requirements.txt     # Зависимости
└── .env.example        # Пример переменных окружения
```

## 🚀 Быстрый старт

### 1. Копирование шаблона

```bash
# Создайте новую папку для вашего проекта
mkdir my-education-bot
cd my-education-bot

# Скопируйте файлы шаблона
cp -r ../Библиотека\ шаблонов/telegram-bot-obuchenie/* .
```

### 2. Настройка окружения

```bash
# Создайте виртуальное окружение
python -m venv venv
source venv/bin/activate  # для Linux/Mac
# или
venv\Scripts\activate     # для Windows

# Установите зависимости
pip install -r requirements.txt
```

### 3. Настройка переменных

Скопируйте `.env.example` в `.env` и заполните свои данные:

```bash
cp .env.example .env
```

Откройте `.env` и заполните:

```
BOT_TOKEN=ваш_токен_от_BotFather
ADMIN_IDS=5690724590,ваш_id
GEMINI_API_KEY=ваш_api_ключ
PAYMENT_PROVIDER_TOKEN=токен_юкассы
DB_PATH=bot_obucheniya.db
```

### 4. Запуск бота

```bash
python bot.py
```

## 📋 Функциональность

### 👥 Управление пользователями
- Регистрация и авторизация
- Премиум-доступ по подписке
- Отслеживание прогресса обучения

### 📚 Система обучения
- Модульная структура курсов
- Разблокировка контента по мере прохождения
- Тестирование с автоматической проверкой

### 💳 Платежи
- Интеграция с ЮKassa
- Автоматическое открытие премиум-доступа
- Управление подписками

### 📊 Аналитика
- Статистика по пользователям
- Отслеживание прогресса
- Административная панель

## ⚙️ Настройка курсов

Откройте `config.py` и настройте модули обучения:

```python
MODULES = {
    1: {
        "title": "Блок 1: Основы рынка",
        "free": True,
        "description": "Бесплатный вводный блок"
    },
    2: {
        "title": "Блок 2: Техники продаж",
        "free": False,
        "description": "Платный блок"
    }
    # Добавляйте свои модули
}
```

## 🔧 Интеграция платежей

### ЮKassa (Рекомендуется)
1. Зарегистрируйтесь в [ЮKassa](https://yookassa.ru/)
2. Получите API ключ
3. Добавьте в `.env`:
   ```
   PAYMENT_PROVIDER_TOKEN=ваш_токен_юкассы
   PREMIUM_PRICE_RUB=4990
   ```

### Telegram Payments
1. Настройте платежи в [@BotFather](https://t.me/BotFather)
2. Добавьте в `config.py`:
   ```python
   PAYMENT_PROVIDER_TOKEN = "ваш_токен_telegram_payments"
   ```

## 🎨 Кастомизация

### Изменение брендинга
- Откройте `templates/messages.py`
- Измените тексты сообщений под ваш бренд
- Обновите кнопки и команды

### Добавление новых функций
1. Создайте новый файл в `handlers/`
2. Добавьте импорт в `bot.py`
3. Зарегистрируйте обработчики

### Интеграция с AI
В шаблоне уже есть интеграция с Gemini AI:

```python
from services.gemini_service import GeminiService

gemini = GeminiService(api_key=GEMINI_API_KEY)
response = await gemini.check_test_answers(question, user_answer)
```

## 📊 Администрирование

### Команды администратора
- `/stats` - статистика по пользователям
- `/users` - список всех пользователей
- `/broadcast` - рассылка сообщения
- `/premium <user_id>` - выдать премиум

### Просмотр статистики
```python
# Получить статистику
from db import count_users, count_premium_users

total_users = await count_users()
premium_users = await count_premium_users()
```

## 🔒 Безопасность

### Защита данных
- Все пользовательские данные хранятся в SQLite
- Платежные данные не сохраняются
- Соответствие 152-ФЗ для РФ

### Рекомендации
1. Используйте `.env` для секретных данных
2. Не храните платежные данные в базе
3. Регулярно делайте backup базы данных

## 🚀 Деплой

### На VPS/Сервере
```bash
# Установите supervisor
sudo apt install supervisor

# Создайте конфиг /etc/supervisor/conf.d/bot.conf
[program:bot]
command=/path/to/venv/bin/python bot.py
directory=/path/to/bot
user=botuser
autostart=true
autorestart=true
```

### Использование Docker
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
CMD ["python", "bot.py"]
```

## 🐛 Частые проблемы

### Бот не отвечает
- Проверьте токен в `.env`
- Убедитесь, что бот запущен
- Проверьте логи ошибок

### Платежи не работают
- Проверьте токен платежной системы
- Убедитесь, что тарифный план подключен
- Проверьте вебхуки для ЮKassa

### База данных не создается
- Проверьте права на запись
- Убедитесь, что SQLite установлен
- Проверьте путь в `DB_PATH`

## 📞 Поддержка

Если возникли вопросы:
- Telegram: @anton_tsoy
- Документация Hermes: https://hermes-agent.nousresearch.com/docs

---

*Этот шаблон основан на реальном рабочем боте @Sreda_academy_bot*