from telegram import Update
from telegram.ext import Application, MessageHandler, filters, CallbackContext, JobQueue
import logging
import os
import asyncio
import nest_asyncio
from datetime import datetime, timedelta
from handlers import handle_message
from ai_summariser import summarise_messages
from weather import register_weather_handler
from random_insult import register_insult_handler
from imdb import register_imdb_handler

# Enable logging
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Load bot token from environment variables
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN environment variable is not set!")

# Store messages
message_log = []

# Main function to run the bot
async def main():
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
    logger.info("Bot is running...")
    await app.run_polling()

if __name__ == "__main__":
    nest_asyncio.apply()
    asyncio.run(main())
