"""
Main bot module that initializes the Telegram bot and registers command handlers.
"""

from datetime import time
import asyncio
import os
import sys
import nest_asyncio
from telegram.ext import Application, MessageHandler, CommandHandler, filters, CallbackQueryHandler
from weather import register_weather_handler
from random_insult import register_insult_handler
from imdb import register_imdb_handler
from convert import register_brl_handler
from dadjokes import register_dadjokes_handler
from handlers import handle_message, summary_command, handle_summary_selection
from message_store import purge_old_messages
from summarizer import daily_group_summary
from brlusdgraph import register_brlusdgraph_handler
from btcusdgraph import register_btcusdgraph_handler
from currencyconverter import register_converter_handler
from currencyconverter import register_currency_handler

# Debugging
print("Python executable:", sys.executable)

# Load bot token from environment variables
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN environment variable is not set!")

async def main():
    """Main function to run the Telegram bot."""
    app = Application.builder().token(TOKEN).build()

    # ✅ Register handlers
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CommandHandler("summary", summary_command))
    app.add_handler(CallbackQueryHandler(handle_summary_selection))  # ✅ Ensure button clicks are handled
  

    # ✅ Start job queue (ensure it is running)
    job_queue = app.job_queue
    if not job_queue:
        print("[ERROR] job_queue is missing!")
    else:
        print("[DEBUG] job_queue is active.")

    job_queue.run_repeating(purge_old_messages, interval=3600, first=3600) # Every hour
    job_queue.run_daily(daily_group_summary, time=time(0, 0)) # Run at midnight

    # Register command handlers
    register_weather_handler(app)
    register_insult_handler(app)
    register_imdb_handler(app)
    register_brl_handler(app)
    register_dadjokes_handler(app)
    register_brlusdgraph_handler(app)
    register_btcusdgraph_handler(app)
    register_converter_handler(app)
    register_currency_handler(app)
    
    print("\n### Bot started! ###\n")

    # Start bot
    await app.run_polling()

if __name__ == "__main__":
    nest_asyncio.apply()
    asyncio.run(main())
