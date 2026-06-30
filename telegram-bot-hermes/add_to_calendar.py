#!/usr/bin/env python3
"""
CLI helper to add events/tasks to Google Calendar using Hermes Bot calendar service.
Usage: python add_to_calendar.py "meeting details"
"""
import sys
import asyncio
from dotenv import load_dotenv

# Load env variables before importing config
load_dotenv()

import calendar_service
import config

async def main():
    if len(sys.argv) < 2:
        print("Error: Please provide event details as an argument.")
        print('Usage: python add_to_calendar.py "Встреча завтра в 15:00"')
        sys.exit(1)
        
    text = sys.argv[1]
    
    # Simple check of webhook configuration
    if not config.GOOGLE_CALENDAR_WEBHOOK_URL:
        print("Error: GOOGLE_CALENDAR_WEBHOOK_URL is not set in .env file.")
        sys.exit(1)
        
    print(f"Parsing and sending event: '{text}'...")
    result = await calendar_service.process_and_add_to_calendar(text)
    
    if result:
        print("\nSuccess! Added to Google Calendar:")
        print(f"📌 Title: {result['title']}")
        print(f"📅 Start: {result['start']}")
        print(f"⌛ End: {result['end']}")
        if result.get('all_day'):
            print("🕒 Duration: All day")
        print(f"📁 Calendar: {result['calendar_name']}")
    else:
        print("\nCould not add to calendar. Either no event details were found in the text, or the Webhook failed.")

if __name__ == "__main__":
    asyncio.run(main())
