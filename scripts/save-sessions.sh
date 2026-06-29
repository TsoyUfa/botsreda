#!/bin/bash

# Скрипт автоматического сохранения сессий Hermes в Obsidian
# Сохраняет важные диалоги, решения и выводы в структурированном виде

# Конфигурация
VAULT_PATH="/Users/anton_tsoy/Desktop/Обсидиан"
SESSION_LOG_DIR="$VAULT_PATH/2. План/conclusions"
DASHBOARD_FILE="$VAULT_PATH/1. Бизнес/00-dashboard.md"
DECISION_LOG="$VAULT_PATH/2. План/decision-log.md"

# Создаем директорию если не существует
mkdir -p "$SESSION_LOG_DIR"

# Функция для создания файла сессии
create_session_file() {
    local session_title="$1"
    local session_content="$2"
    local session_type="$3"  # business, plan, clone, mastery
    
    # Генерируем имя файла
    local timestamp=$(date +"%Y-%m-%d_%H-%M")
    local filename="${timestamp}_${session_title// /_-}.md"
    local filepath="$SESSION_LOG_DIR/$filename"
    
    # Определяем категорию
    local category=""
    case $session_type in
        "business") category="1. Бизнес" ;;
        "plan") category="2. План" ;;
        "clone") category="3. Мой клон" ;;
        "mastery") category="4. Мастерство" ;;
        *) category="Общее" ;;
    esac
    
    # Создаем содержимое файла
    cat > "$filepath" << EOF
# $session_title

**Категория:** $category  
**Дата:** $(date +"%Y-%m-%d %H:%M")  
**Тип:** Сессия Hermes

## Краткое описание
Автоматически сохраненная сессия Hermes с ключевыми выводами и решениями.

## Содержание сессии
$session_content

## Ключевые решения
$(extract_decisions "$session_content")

## Следующие шаги
$(extract_next_steps "$session_content")

## Связи
[[$session_title]]
[[decision-log]]

---
*Автоматически создано: $(date)*
*Система: Hermes Agent*
EOF

    echo "Сессия сохранена: $filepath"
}

# Функция для извлечения решений из текста
extract_decisions() {
    local text="$1"
    echo "$text" | grep -i "решил\|решение\|будем\|сделаем\|начнем" | head -5 | sed 's/^/- /'
}

# Функция для извлечения следующих шагов
extract_next_steps() {
    local text="$1"
    echo "$text" | grep -i "следующ\|следующ\|дальше\|далее\|следует" | head -3 | sed 's/^/- /'
}

# Функция для обновления дашборда
update_dashboard() {
    if [[ -f "$DASHBOARD_FILE" ]]; then
        # Добавляем информацию о последней сессии
        local session_info="\\n- **Последняя сессия:** $(date +"%Y-%m-%d %H:%M") - "
        session_info+="Обновлен вывод в conclusions/"
        
        # Добавляем в начало файла после заголовка
        sed -i '' "2a\\$session_info" "$DASHBOARD_FILE"
        echo "Дашборд обновлен"
    fi
}

# Функция для добавления в журнал решений
add_to_decision_log() {
    local decision="$1"
    local context="$2"
    
    if [[ -f "$DECISION_LOG" ]]; then
        cat >> "$DECISION_LOG" << EOF

### $(date +"%Y-%m-%d %H:%M") - Автоматическая сессия

**Решение:** $decision  
**Контекст:** $context  
**Источник:** Сессия Hermes

---
EOF
        echo "Решение добавлено в журнал"
    fi
}

# Основная функция обработки сессии
process_session() {
    echo "Обработка сессии Hermes..."
    
    # Получаем последние сообщения из Hermes (имитация)
    # В реальной ситуации здесь будет парсинг логов Hermes
    local session_title="Автоматическая сессия $(date +"%d.%m.%Y")"
    local session_content="Содержание сессии с ключевыми решениями и выводами."
    local session_type="business"  # Можно определить автоматически
    
    # Создаем файл сессии
    create_session_file "$session_title" "$session_content" "$session_type"
    
    # Обновляем дашборд
    update_dashboard
    
    # Добавляем решение в журнал
    add_to_decision_log "Автоматическая обработка сессии" "Регулярное сохранение важных диалогов"
    
    echo "Сессия успешно обработана и сохранена"
}

# Функция для анализа содержимого и определения типа
analyze_content_type() {
    local content="$1"
    
    # Проверяем ключевые слова для определения типа
    if echo "$content" | grep -qi "деньги\|клиент\|продаж\|оффер\|партнер\|сделка"; then
        echo "business"
    elif echo "$content" | grep -qi "задач\|план\|проект\|дедлайн\|цель"; then
        echo "plan"
    elif echo "$content" | grep -qi "я\|мой\|личн\|стиль\|голос"; then
        echo "clone"
    elif echo "$content" | grep -qi "метод\|фреймворк\|эксперт\|практик\|стандарт"; then
        echo "mastery"
    else
        echo "general"
    fi
}

# Cron-задача для ежедневного сохранения
daily_session_save() {
    echo "Ежедневное сохранение сессий..."
    
    # Проверяем наличие новых сессий
    # В реальной ситуации здесь будет проверка логов Hermes
    local has_new_sessions=true
    
    if [[ "$has_new_sessions" == true ]]; then
        process_session
    fi
}

# Функция для ручного сохранения текущей сессии
save_current_session() {
    local title="$1"
    local content="$2"
    
    if [[ -z "$title" ]]; then
        title="Сессия $(date +"%d.%m.%Y %H:%M")"
    fi
    
    if [[ -z "$content" ]]; then
        content="Содержание сессии не предоставлено"
    fi
    
    local session_type=$(analyze_content_type "$content")
    create_session_file "$title" "$content" "$session_type"
}

# Обработка аргументов командной строки
case "${1:-}" in
    "daily")
        daily_session_save
        ;;
    "manual")
        save_current_session "$2" "$3"
        ;;
    "process")
        process_session
        ;;
    *)
        echo "Использование:"
        echo "  $0 daily              - Ежедневное сохранение сессий"
        echo "  $0 manual [title] [content] - Ручное сохранение сессии"
        echo "  $0 process           - Обработка текущей сессии"
        exit 1
        ;;
esac

exit 0