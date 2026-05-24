# Структура проекта iOS приложения

## Обзор архитектуры

Приложение использует архитектуру **MVVM (Model-View-ViewModel)** с использованием **SwiftUI** и **Combine**.

## Детальная структура

```
AnonymousRealEstate/
│
├── App/                          # Точка входа приложения
│   ├── AnonymousRealEstateApp.swift
│   └── ContentView.swift
│
├── Models/                       # Модели данных
│   ├── User.swift                # Пользователь (реальный + анонимное имя)
│   ├── Message.swift             # Сообщение в ветке
│   ├── Thread.swift              # Ветка диалога
│   └── AnonymousName.swift       # Анонимное имя
│
├── Views/                        # SwiftUI представления
│   ├── Main/
│   │   ├── MainView.swift        # Главный экран
│   │   └── ThreadListView.swift  # Список веток
│   ├── Chat/
│   │   ├── ChatView.swift        # Экран чата
│   │   └── MessageBubbleView.swift # Пузырь сообщения
│   ├── Profile/
│   │   ├── ProfileView.swift      # Профиль пользователя
│   │   └── SubscriptionView.swift # Управление подписками
│   ├── Settings/
│   │   └── SettingsView.swift     # Настройки
│   └── Auth/
│       └── AuthView.swift         # Экран авторизации
│
├── Services/                     # Бизнес-логика и сервисы
│   ├── AuthService.swift          # Аутентификация
│   ├── TelegramService.swift      # Работа с Telegram API
│   ├── MessageService.swift       # Работа с сообщениями
│   └── AnonymousNameService.swift # Генерация анонимных имён
│
├── ViewModels/                    # ViewModels для MVVM
│   ├── MainViewModel.swift        # ViewModel главного экрана
│   ├── ChatViewModel.swift        # ViewModel чата
│   └── ProfileViewModel.swift     # ViewModel профиля
│
└── Utils/                         # Утилиты
    ├── Constants.swift            # Константы приложения
    └── Extensions.swift           # Расширения Swift
```

## Описание компонентов

### Models (Модели данных)

**User.swift**
- Хранит информацию о пользователе
- Связывает реальное имя с анонимным
- Управляет типом подписки

**Message.swift**
- Сообщение в ветке диалога
- Содержит анонимное имя автора
- Поддерживает лайки

**Thread.swift**
- Ветка диалога (тема обсуждения)
- Категории: застройщики, цены, проблемы, советы, вопросы
- Может быть закреплена или закрыта

**AnonymousName.swift**
- Генерирует случайные анонимные имена
- Формат: `Случайный_Пользователь_1234`

### Services (Сервисы)

**AuthService**
- Управляет аутентификацией
- Сохраняет пользователя локально
- Обновляет подписки

**TelegramService**
- Интеграция с Telegram Bot API
- Отправка и получение сообщений
- Работа с ветками

**MessageService**
- Отправка сообщений
- Загрузка сообщений ветки
- Управление состоянием

**AnonymousNameService**
- Генерация новых анонимных имён
- Сохранение текущего имени
- История имён

### ViewModels

**MainViewModel**
- Загрузка списка веток
- Популярные ветки
- Состояние загрузки

**ChatViewModel**
- Загрузка сообщений ветки
- Отправка новых сообщений
- Обновление UI

**ProfileViewModel**
- Статистика пользователя
- Загрузка данных профиля

### Views

**MainView**
- Главный экран приложения
- Приветствие
- Статистика
- Популярные ветки
- Категории

**ThreadListView**
- Список всех веток
- Фильтрация по категориям
- Создание новых веток

**ChatView**
- Экран чата ветки
- Список сообщений
- Поле ввода

**ProfileView**
- Профиль пользователя
- Статистика
- Управление подпиской
- Настройки

## Потоки данных

### Аутентификация
```
AuthView → AuthService → UserDefaults → ContentView
```

### Отправка сообщения
```
ChatView → ChatViewModel → MessageService → TelegramService → API
```

### Загрузка веток
```
MainView → MainViewModel → TelegramService → API → UI Update
```

## Зависимости

- **SwiftUI** - UI фреймворк
- **Combine** - реактивное программирование
- **Foundation** - базовые типы
- **UserDefaults** - локальное хранение (можно заменить на Core Data)

## Расширяемость

### Добавление новых функций

1. **Push-уведомления**
   - Добавить `NotificationService`
   - Интегрировать с Firebase Cloud Messaging

2. **Офлайн-режим**
   - Добавить Core Data
   - Синхронизация при подключении

3. **In-App Purchases**
   - Добавить `SubscriptionService`
   - Интеграция с StoreKit

4. **Аналитика**
   - Добавить `AnalyticsService`
   - Интеграция с Firebase Analytics

## Безопасность

- Токен Telegram Bot API хранится в коде (для продакшена использовать Keychain)
- Анонимные имена генерируются локально
- Связь реального пользователя и анонимного имени хранится только локально
- Для продакшена нужен сервер для безопасного хранения данных



