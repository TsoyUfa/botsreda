#!/usr/bin/env python3
"""
Script to send daily summary to Telegram
"""

import os
import requests
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def send_telegram_message(message, bot_token=None, chat_id=None):
    """
    Send a message to Telegram using the Bot API
    
    Args:
        message (str): The message to send
        bot_token (str): Telegram bot token (defaults to environment variable)
        chat_id (str): Chat ID to send the message to (defaults to environment variable)
    
    Returns:
        bool: True if successful, False otherwise
    """
    # Get credentials from parameters or environment variables
    bot_token = bot_token or os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = chat_id or os.getenv('TELEGRAM_CHAT_ID')
    
    if not bot_token or not chat_id:
        logger.error("Missing Telegram credentials. Please set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID environment variables.")
        return False
    
    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        data = {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "Markdown"
        }
        
        response = requests.post(url, json=data)
        response.raise_for_status()
        
        logger.info("Message sent successfully to Telegram")
        return True
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to send message to Telegram: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return False

def get_daily_summary_template():
    """
    Generate the daily summary template
    
    Returns:
        str: The formatted daily summary message
    """
    today = datetime.now().strftime("%d.%m.%Y")
    
    template = f"""🌆 **ИТОГИ ДНЯ** - {today}

Пожалуйста, наговорите голосовым сообщением или напишите текстом:

✅ **Что сделано сегодня?**
❌ **Что не успели?**
💡 **Какие инсайты или решения?**
📋 **Что перенести на завтра?**

Для голоса: зажмите микрофон 🎤 и говорите. Для текста: просто напишите ответ здесь.

---
Ваши ответы будут автоматически обработаны и добавлены в базу знаний."""
    
    return template

def main():
    """Main function to send the daily summary"""
    logger.info("Preparing to send daily summary to Telegram...")
    
    # Get the template
    message = get_daily_summary_template()
    
    # Send the message
    success = send_telegram_message(message)
    
    if success:
        logger.info("Daily summary sent successfully!")
        return 0
    else:
        logger.error("Failed to send daily summary.")
        return 1

if __name__ == "__main__":
    exit(main())