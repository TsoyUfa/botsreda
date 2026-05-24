# Инструкция по установке и настройке

## Требования

- macOS 13.0+ (Ventura или новее)
- Xcode 15.0+
- iOS 16.0+ (для тестирования на устройстве)
- Аккаунт Apple Developer (для публикации в App Store)

## Шаги установки

### 1. Создание проекта в Xcode

1. Откройте Xcode
2. Выберите `File > New > Project`
3. Выберите `iOS > App`
4. Заполните:
   - **Product Name:** `AnonymousRealEstate`
   - **Team:** Ваша команда разработчика
   - **Organization Identifier:** `com.antontsoy` (или ваш)
   - **Interface:** `SwiftUI`
   - **Language:** `Swift`
   - **Storage:** `None` (или Core Data, если нужна локальная БД)

### 2. Добавление файлов в проект

1. Скопируйте все файлы из этой папки в структуру проекта Xcode:
   - `App/` → добавьте в проект
   - `Models/` → добавьте в проект
   - `Views/` → добавьте в проект
   - `Services/` → добавьте в проект
   - `ViewModels/` → добавьте в проект
   - `Utils/` → добавьте в проект

2. Убедитесь, что все файлы добавлены в Target `AnonymousRealEstate`

### 3. Настройка Telegram Bot API

1. Создайте бота в Telegram через [@BotFather](https://t.me/botfather)
2. Получите токен бота
3. Откройте `Utils/Constants.swift`
4. Замените `YOUR_TELEGRAM_BOT_TOKEN_HERE` на ваш токен:

```swift
static let telegramBotToken = "123456789:ABCdefGHIjklMNOpqrsTUVwxyz"
```

### 4. Настройка Info.plist

Добавьте в `Info.plist`:

```xml
<key>NSAppTransportSecurity</key>
<dict>
    <key>NSAllowsArbitraryLoads</key>
    <false/>
    <key>NSExceptionDomains</key>
    <dict>
        <key>api.telegram.org</key>
        <dict>
            <key>NSExceptionAllowsInsecureHTTPLoads</key>
            <false/>
            <key>NSIncludesSubdomains</key>
            <true/>
        </dict>
    </dict>
</dict>
```

### 5. Настройка Capabilities

В настройках проекта (`Signing & Capabilities`):
- Включите `Push Notifications` (если планируете уведомления)
- Настройте `App Groups` (если нужен общий доступ к данным)

### 6. Запуск приложения

1. Выберите симулятор или устройство
2. Нажмите `Cmd + R` для запуска
3. Приложение должно запуститься и показать экран авторизации

## Настройка бэкенда

### Вариант 1: Использование Telegram Bot API напрямую

Приложение может работать напрямую с Telegram Bot API, но это имеет ограничения:
- Бот не может инициировать диалог с пользователем
- Нужен сервер для полноценной работы

### Вариант 2: Создание собственного API

Рекомендуется создать собственный бэкенд, который:
1. Хранит связь между Telegram ID и анонимными именами
2. Публикует сообщения в Telegram-канал от имени анонимных имён
3. Предоставляет REST API для приложения

Пример структуры API:
- `POST /api/auth` - аутентификация
- `GET /api/threads` - получение списка веток
- `GET /api/threads/:id/messages` - получение сообщений ветки
- `POST /api/threads/:id/messages` - отправка сообщения
- `POST /api/threads` - создание новой ветки

## Тестирование

### Тестовые данные

В коде есть мок-данные для тестирования:
- `User.mock` - тестовый пользователь
- `Message.mock` - тестовое сообщение
- `Thread.mock` - тестовая ветка

### Симулятор

1. Запустите приложение в симуляторе
2. Введите тестовый Telegram ID: `123456789`
3. Введите имя: `Тестовый Пользователь`
4. Нажмите "Войти"

### Реальное устройство

1. Подключите iPhone/iPad
2. Выберите устройство в Xcode
3. Нажмите `Cmd + R`
4. Разрешите установку на устройстве (если нужно)

## Следующие шаги

1. **Интеграция с реальным API** - замените мок-данные на реальные запросы
2. **Добавление Core Data** - для офлайн-режима
3. **Push-уведомления** - для новых сообщений
4. **In-App Purchases** - для подписок
5. **Аналитика** - Firebase Analytics или аналоги
6. **Краш-репорты** - Firebase Crashlytics

## Проблемы и решения

### Ошибка компиляции

- Убедитесь, что все файлы добавлены в Target
- Проверьте версию Swift (должна быть 5.9+)
- Очистите Build Folder (`Cmd + Shift + K`)

### Ошибки при запуске

- Проверьте настройки Signing & Capabilities
- Убедитесь, что Info.plist настроен правильно
- Проверьте токен Telegram Bot API

### Проблемы с сетью

- Проверьте настройки App Transport Security
- Убедитесь, что устройство/симулятор имеет интернет
- Проверьте токен бота

## Поддержка

Если возникли вопросы:
- 📱 Telegram: @antontsoy
- 🌐 Сайт: antontsoy.ru



