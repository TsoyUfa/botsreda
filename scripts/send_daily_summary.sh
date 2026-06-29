#!/bin/bash
# Wrapper script to run the daily summary Telegram sender

# Navigate to the script directory
cd "$(dirname "$0")"

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed"
    exit 1
fi

# Check if requests module is installed
if ! python3 -c "import requests" &> /dev/null; then
    echo "Error: requests module is not installed. Please run: pip3 install requests"
    exit 1
fi

# Check if environment variables are set
if [ -z "$TELEGRAM_BOT_TOKEN" ] || [ -z "$TELEGRAM_CHAT_ID" ]; then
    echo "Error: Please set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID environment variables"
    echo "You can set them in your crontab like this:"
    echo "TELEGRAM_BOT_TOKEN=your_bot_token"
    echo "TELEGRAM_CHAT_ID=your_chat_id"
    exit 1
fi

# Run the Python script
echo "Sending daily summary to Telegram..."
python3 send_daily_summary.py

if [ $? -eq 0 ]; then
    echo "Daily summary sent successfully!"
else
    echo "Failed to send daily summary."
    exit 1
fi