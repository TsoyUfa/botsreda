# Notion Sync for Obsidian

Минимальный двусторонний синк Obsidian <-> Notion для процессов, метрик и финансов.

## Быстрый старт
1. Создай интеграцию в Notion и получи token.
2. Создай страницу-родителя в Notion и поделись ей с интеграцией.
3. Скопируй `config.example.json` в `config.json`.
4. Заполни `parent_page_id` и проверь `vault_root`.
5. Запусти:
   - `NOTION_TOKEN=... python sync.py init --write-config`
   - `NOTION_TOKEN=... python sync.py sync --dry-run`
   - `NOTION_TOKEN=... python sync.py sync`

## Структура в Notion
Скрипт создаст базы:
- `Processes`
- `Tasks`
- `Metrics`
- `Finance`

Все базы используют общий набор свойств из `schema.json`.

## Дашборды (рекомендуемая структура)
Создай страницу `Dashboards` и внутри:
- `Главная` — вид базы `Processes`, фильтр `Status = active`, сортировка по `Due`.
- `Финансы` — вид базы `Finance`, фильтр `Status != archived`, группировка по `Area`.
- `Продажи и маркетинг` — вид базы `Processes`, фильтр `Area in (marketing, sales)`.

## Frontmatter для синка
Минимальные поля:
```
type: process|task|metric|finance
status: active|planned|done|archived|reference|paused
area: expert_city|products|finance|personal_finance|marketing|sales|ops
owner: Anton
review: daily|weekly|monthly|quarterly|none
due: 2026-02-28
kpi: краткий KPI
```

Скрипт добавляет:
- `notion_id`
- `last_synced_at`

## Автоматизация (macOS launchd)
1. Проверь путь в `launchd/com.antontsoy.notion_sync.plist`.
2. Загрузить задачу:
   - `launchctl load ~/Library/LaunchAgents/com.antontsoy.notion_sync.plist`
3. Логи: `logs/launchd.out.log` и `logs/launchd.err.log`.

## Конфликты
Если изменения были и в Obsidian, и в Notion, создается файл в `conflicts/`
с версией из Notion.
