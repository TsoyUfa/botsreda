# Инструкция по установке расширений Cursor

## Быстрая установка через командную строку

Выполните следующие команды в терминале для установки всех рекомендуемых расширений:

### Приоритет 1: Базовый набор (критично)

```bash
# Markdown All in One - базовая работа с документами
cursor --install-extension yzhang.markdown-all-in-one

# Todo Tree - управление задачами
cursor --install-extension Gruntfuggly.todo-tree

# Bookmarks - быстрая навигация
cursor --install-extension alefragnani.Bookmarks
```

### Приоритет 2: Расширенная работа с документами

```bash
# Markdown Preview Enhanced - расширенный предпросмотр
cursor --install-extension shd101wyy.markdown-preview-enhanced

# PDF Preview - просмотр PDF файлов
cursor --install-extension analytic-signal.preview-pdf
```

### Приоритет 3: Работа с данными

```bash
# Database Client - работа с базами данных
cursor --install-extension cweijan.vscode-database-client2

# Rainbow CSV - подсветка CSV файлов
cursor --install-extension mechatroner.rainbow-csv
```

### Приоритет 4: API и интеграции

```bash
# REST Client - тестирование API
cursor --install-extension humao.rest-client
```

### Приоритет 5: Визуализация

```bash
# Mermaid Preview - диаграммы в документах
cursor --install-extension vstirbu.vscode-mermaid-preview
```

## Установка через UI Cursor

Если команды не работают, используйте интерфейс:

1. Откройте панель расширений: `Cmd+Shift+X` (Mac) или `Ctrl+Shift+X` (Windows/Linux)
2. Найдите расширение по ID (например, `yzhang.markdown-all-in-one`)
3. Нажмите "Install" (Установить)
4. Перезапустите Cursor при необходимости

## Автоматическая установка рекомендуемых расширений

После создания файла `.vscode/extensions.json` Cursor предложит установить рекомендуемые расширения:

1. Откройте проект в Cursor
2. Появится уведомление "This workspace has extension recommendations"
3. Нажмите "Install All" или "Show Recommendations"

## Проверка установки

После установки проверьте, что расширения активны:

1. Откройте панель расширений (`Cmd+Shift+X`)
2. В поиске введите "Installed"
3. Убедитесь, что все расширения установлены и включены

## Горячие клавиши

После установки расширений доступны следующие горячие клавиши:

- `Cmd+Shift+V` — предпросмотр Markdown
- `Cmd+K V` — предпросмотр Markdown рядом
- `Cmd+Shift+O` — оглавление документа
- `Cmd+Option+K` — создать/удалить закладку
- `Cmd+Option+J` — следующая закладка
- `Cmd+Option+L` — предыдущая закладка

## Настройка Todo Tree

Todo Tree уже настроен для работы с русскими тегами:
- `TODO` — обычные задачи
- `ВАЖНО` — важные задачи (оранжевый)
- `ИДЕЯ` — идеи (бирюзовый)
- `FIXME` — исправления (красный)
- `NOTE` — заметки (синий)

Используйте эти теги в документах:
```markdown
- [ ] TODO: Встретиться с застройщиком
- [ ] ВАЖНО: Подготовить презентацию для клиента
- [ ] ИДЕЯ: Создать новый продукт для риэлторов
```

## Следующие шаги

1. Установите расширения из Приоритета 1 (базовый набор)
2. Протестируйте на реальных документах
3. Постепенно добавляйте расширения из других приоритетов
4. Настройте под свои предпочтения
