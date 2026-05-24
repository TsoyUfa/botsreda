# Cursor Skills — Obsidian vault

**Хранение:** проектные skills в `.cursor/skills/` (развиваются вместе с vault).  
Персональные копии при необходимости: `~/.cursor/skills/`.

## Карта skills

| Skill | Задача | Не дублирует |
|-------|--------|--------------|
| `business-decision-router` | ROI, приоритеты, 24ч, бэклог | `/biz` (роутер), `/storm` (идеи) |
| `real-estate-offer-architect` | КП, оффер, 30/60/90 | `/slides` (только структура слайдов) |
| `second-brain-triage` | Куда положить заметки, 4 папки | `/knowledge` (одна заметка → действие) |
| `crm-funnel-diagnostician` | Воронка, SLA, GAP, MVP 7–14 дней | — |
| `cursor-workflow-coach` | Смыслокодинг: планы, фазы, MVP, Cursor vs Claude Code | `delivery-to-result-flow`, `mvp-money-filter` |
| `anton-voice` | Tone of Voice Антона | `social-post`, `carousel`, `reels-ideas` (формат) |
| `social-post` | Текст поста по платформе | `anton-voice` (голос) |
| `carousel` | Слайды карусели | `anton-voice` |
| `reels-ideas` | Идеи Reels | `anton-voice`, `content-funnel-builder` (волна 2) |

## Commands (`.cursor/commands/`)

- `/biz` → начни с `business-decision-router` при смешанном запросе
- `/storm` → штурм; финал можно через `business-decision-router`
- `/knowledge` → одна заметка; массово → `second-brain-triage`
- `/slides` → слайды; смысл КП → `real-estate-offer-architect`
- `/site-edit` → ТЗ на лендинг (без отдельного skill)

## Вызов

Упомяни имя skill в чате, например: «используй skill `crm-funnel-diagnostician` для этой воронки».

## Rules (смыслокодинг)

- `delivery-to-result-flow.mdc` — research → план → фазы → деплой
- `mvp-money-filter.mdc` — фильтр 500k+ / 7 дней
- `security-pd-review.mdc` — ПДн, .env, CRM

## Волна 2 (план, не создано)

- `agent-training-designer`
- `content-funnel-builder`
- `meeting-to-action`
- `transurfing-business-check`
