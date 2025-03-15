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
from convert import register_brl_handler
from dadjokes import register_dadjokes_handler

# Load bot token from environment variables
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN environment variable is not set!")

# Store messages
message_log = []

async def main():
    """Main function to run the Telegram bot."""
    app = Application.builder().token(TOKEN).build()

    # Registering all handlers
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    register_weather_handler(app)
    register_insult_handler(app)
    register_imdb_handler(app)
    register_brl_handler(app)
    register_dadjokes_handler(app)

    # Schedule summary every hour
    job_queue = app.job_queue
    job_queue.run_repeating(summarise_messages, interval=3600, first=0)

    # Start bot
    await app.run_polling()

if __name__ == "__main__":
    nest_asyncio.apply()
    asyncio.run(main())
