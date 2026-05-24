# Децентрализованная анонимная сеть недвижимости - iOS App

## Описание

iOS приложение для децентрализованной анонимной сети недвижимости, где участники общаются без раскрытия личности. При каждом входе пользователь получает случайное имя.

## Технологии

- **Swift 5.9+**
- **SwiftUI** - современный UI фреймворк
- **Combine** - реактивное программирование
- **Telegram Bot API** - интеграция с Telegram
- **Core Data** - локальное хранение данных

## Структура проекта

```
AnonymousRealEstate/
├── App/
│   ├── AnonymousRealEstateApp.swift      # Точка входа приложения
│   └── ContentView.swift                 # Главный экран
├── Models/
│   ├── User.swift                        # Модель пользователя
│   ├── Message.swift                     # Модель сообщения
│   ├── Thread.swift                      # Модель ветки диалога
│   └── AnonymousName.swift               # Модель анонимного имени
├── Views/
│   ├── Main/
│   │   ├── MainView.swift                # Главный экран
│   │   └── ThreadListView.swift          # Список веток
│   ├── Chat/
│   │   ├── ChatView.swift                # Экран чата
│   │   └── MessageBubbleView.swift       # Пузырь сообщения
│   ├── Profile/
│   │   ├── ProfileView.swift              # Профиль пользователя
│   │   └── SubscriptionView.swift         # Подписки
│   └── Settings/
│       └── SettingsView.swift             # Настройки
├── Services/
│   ├── TelegramService.swift             # Сервис для работы с Telegram
│   ├── AnonymousNameService.swift        # Сервис генерации имён
│   ├── MessageService.swift              # Сервис работы с сообщениями
│   └── AuthService.swift                 # Сервис аутентификации
├── ViewModels/
│   ├── MainViewModel.swift               # ViewModel для главного экрана
│   ├── ChatViewModel.swift                # ViewModel для чата
│   └── ProfileViewModel.swift            # ViewModel для профиля
└── Utils/
    ├── Constants.swift                   # Константы
    └── Extensions.swift                  # Расширения
```

## Установка

1. Откройте проект в Xcode 15.0+
2. Установите зависимости (если используются)
3. Настройте Telegram Bot API токен в `Constants.swift`
4. Запустите приложение

## Основные функции

- ✅ Анонимная регистрация
- ✅ Случайные имена при каждом входе
- ✅ Создание и участие в ветках диалогов
- ✅ Отправка анонимных сообщений
- ✅ Просмотр популярных веток
- ✅ Система подписок (Базовый, Премиум, Про)
- ✅ Аналитика для создателя

## Требования

- iOS 16.0+
- Xcode 15.0+
- Swift 5.9+

## Автор

Антон Цой | Эксперт по недвижимости



