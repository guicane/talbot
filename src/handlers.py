"""
Module for handling Telegram messages by reacting with emojis or stickers.
"""

import logging
from datetime import datetime

from telegram import Update
from telegram.ext import CallbackContext

# Get the module-specific logger; logging configuration is done centrally.
logger = logging.getLogger(__name__)

# Define keyword-to-emoji mapping
KEYWORDS = {
    "cunts": "🍑",
}

# Custom sticker mapping; broken into two lines to respect the line length limit
STICKERS = {
    "not worthwhile": (
        "CAACAgQAAxkBAAEN7OJnw47vgltrMdG3wA9dbm8P-Gq36gACPA0AAscocVEUPP2ID"
        "SRDKDYE"
    )
}

# Store messages
message_log = []


async def handle_message(update: Update, context: CallbackContext) -> None:
    """
    Process incoming messages and respond with a sticker or emoji based on triggers.

    Logs the message with a timestamp, then checks for any sticker or emoji triggers.
    If a sticker trigger is found, sends the corresponding sticker and stops further processing.
    Otherwise, checks for emoji triggers and reacts to the first match found.
    """
    message_text = update.message.text.lower()
    chat_id = update.message.chat_id

    # Log message with timestamp
    message_log.append((datetime.utcnow(), chat_id, update.message.text))

    # Check for sticker triggers
    for keyword, sticker_id in STICKERS.items():
        if keyword in message_text:
            await context.bot.send_sticker(chat_id=chat_id, sticker=sticker_id)
            return

    # Check for emoji triggers
    for keyword, emoji in KEYWORDS.items():
        if keyword in message_text:
            await context.bot.send_message(chat_id=chat_id, text=emoji)
            break
