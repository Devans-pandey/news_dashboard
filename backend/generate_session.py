"""
🔑 Generate a Telegram StringSession for Render deployment.

Run this ONCE locally:
    python generate_session.py

It will ask for your phone number and OTP code.
Then it prints a session string — copy it and add it as
TELEGRAM_SESSION env var on Render.
"""

import os
import asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession

API_ID = int(input("Enter your TELEGRAM_API_ID: "))
API_HASH = input("Enter your TELEGRAM_API_HASH: ")


async def main():
    client = TelegramClient(StringSession(), API_ID, API_HASH)
    await client.start()

    session_string = client.session.save()

    print("\n" + "=" * 60)
    print("✅ YOUR TELEGRAM SESSION STRING (copy this):")
    print("=" * 60)
    print(session_string)
    print("=" * 60)
    print("\n📋 Add this as TELEGRAM_SESSION env var on Render.")

    await client.disconnect()


asyncio.run(main())
