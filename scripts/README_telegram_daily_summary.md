# Telegram Daily Summary Script

This script sends a daily summary template to Telegram in Russian, prompting for completed tasks, pending items, insights, and tomorrow's plans.

## Setup Instructions

### 1. Create a Telegram Bot

1. Open Telegram and search for the "BotFather" bot
2. Start a chat with BotFather and send `/newbot`
3. Follow the prompts to name your bot and get a **Bot Token**
4. Save the token somewhere secure - you'll need it for the next step

### 2. Get Your Chat ID

1. Add your bot to a conversation (or start a chat with it)
2. Send any message to the bot
3. Visit this URL in your browser (replace YOUR_BOT_TOKEN with your actual token):
   ```
   https://api.telegram.org/botYOUR_BOT_TOKEN/getUpdates
   ```
4. Look for the "chat" -> "id" value in the response - this is your **Chat ID**

### 3. Install Dependencies

```bash
pip3 install requests
```

### 4. Set Environment Variables

For manual execution:
```bash
export TELEGRAM_BOT_TOKEN="your_bot_token_here"
export TELEGRAM_CHAT_ID="your_chat_id_here"
```

For cron job, add them before your command:
```
TELEGRAM_BOT_TOKEN=your_bot_token TELEGRAM_CHAT_ID=your_chat_id /path/to/scripts/send_daily_summary.sh
```

Or create a `.env` file in the scripts directory:
```
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
```

## Usage

### Manual Execution

```bash
# Make the script executable first
chmod +x scripts/send_daily_summary.sh

# Run the script
scripts/send_daily_summary.sh
```

### Cron Job Setup

To run this automatically every day at 6 PM (18:00):

1. Edit your crontab:
   ```bash
   crontab -e
   ```

2. Add this line:
   ```
   0 18 * * * TELEGRAM_BOT_TOKEN=your_bot_token TELEGRAM_CHAT_ID=your_chat_id /Users/anton_tsoy/Desktop/Обсидиан/scripts/send_daily_summary.sh >> /Users/anton_tsoy/Desktop/Обсидиан/scripts/daily_summary.log 2>&1
   ```

3. Save and exit

## What the Script Does

The script sends a message in this format:

```
🌆 **ИТОГИ ДНЯ** - [today's date]

Пожалуйста, наговорите голосовым сообщением или напишите текстом:

✅ **Что сделано сегодня?**
❌ **Что не успели?**
💡 **Какие инсайты или решения?**
📋 **Что перенести на завтра?**

Для голоса: зажмите микрофон 🎤 и говорите. Для текста: просто напишите ответ здесь.

---
Ваши ответы будут автоматически обработаны и добавлены в базу знаний.
```

## Troubleshooting

- **"Module not found" error**: Make sure you've installed the requests module: `pip3 install requests`
- **"Missing credentials" error**: Double-check that your environment variables are set correctly
- **"Invalid token" error**: Verify your bot token is correct and hasn't expired
- **"Chat not found" error**: Make sure your chat ID is correct and that you've sent at least one message to your bot first

## Files

- `send_daily_summary.py` - Main Python script that sends the message
- `send_daily_summary.sh` - Shell wrapper that checks dependencies and runs the Python script

## Security Note

Never commit your bot token or chat ID to version control. Always use environment variables or secure configuration files for sensitive information.