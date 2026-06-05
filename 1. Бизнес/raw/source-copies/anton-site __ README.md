# Сайт-визитка · Антон Цой

Neo-brutalism MVP: главная, кейсы, форма заявки, Telegram.

## Локальный просмотр

```bash
cd anton-site
python3 -m http.server 8080
```

Открой http://localhost:8080

> Форма на localhost откроет Telegram с готовым текстом (API работает только после деплоя).

## Деплой на Vercel (через Cursor)

1. Создай репозиторий на GitHub и залей папку `anton-site` (или весь репо с root = `anton-site`).
2. На [vercel.com](https://vercel.com) → Import Project → выбери репо.
3. **Root Directory:** `anton-site` (если сайт в подпапке).
4. **Environment Variables:**
   - `TELEGRAM_BOT_TOKEN` — токен от [@BotFather](https://t.me/BotFather)
   - `TELEGRAM_CHAT_ID` — твой chat id (напиши боту, узнай через getUpdates)
5. Deploy.

После деплоя форма шлёт заявки в Telegram.

## Редактирование

| Файл | Что менять |
|------|------------|
| `index.html` | Тексты, кейсы, ссылки |
| `css/main.css` | Цвета, отступы, стиль |
| `js/main.js` | Логика формы |
| `api/lead.js` | Формат сообщения в Telegram |

Команда в Cursor: *«Добавь кейс про …»*, *«Смени акцент на жёлтый»*, *«Выложи на Vercel»*.

## Контакты по умолчанию

- Telegram: [@antontsoy](https://t.me/antontsoy)
- Email в шаблоне: `hello@antontsoy.ru` — замени на рабочий.
