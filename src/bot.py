"""
Main bot module that initializes the Telegram bot and registers command handlers.
"""

import asyncio
import os
import nest_asyncio
from telegram.ext import Application, MessageHandler, filters
from handlers import handle_message
from ai_summariser import summarise_messages
from weather import register_weather_handler
from random_insult import register_insult_handler
from imdb import register_imdb_handler
from logging_config import setup_logging

setup_logging()

# Load bot token from environment variables
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN environment variable is not set!")

# Store messages
message_log = []


async def main():
    """Main function to run the Telegram bot."""
    app = Application.builder().token(TOKEN).build()

    # Add message handler
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Add weather handler
    register_weather_handler(app)

    # Add insult handler
    register_insult_handler(app)

    # Add imdb handler
    register_imdb_handler(app)

    # Schedule summary every hour
    job_queue = app.job_queue
    job_queue.run_repeating(summarise_messages, interval=3600, first=0)

    # Start bot
    await app.run_polling()


if __name__ == "__main__":
    nest_asyncio.apply()
    asyncio.run(main())
