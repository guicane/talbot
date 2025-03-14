"""
Module for handling Telegram messages by reacting with emojis or stickers.
"""

from datetime import datetime

from telegram import Update
from telegram.ext import CallbackContext


KEYWORDS = {
    "cunts": "🍑",
}

STICKERS = {
    "not worthwhile": "CAACAgQAAxkBAAEN7OJnw47vgltrMdG3wA9dbm8P-Gq36gACPA0AAscocVEUPP2IDSRDKDYE"
}

GIFS = {
    "informer": "https://media3.giphy.com/media/"
    "v1.Y2lkPTc5MGI3NjExcG0yODg0dXF2bml5YWhrc24ycmpxOTl3dnF6cGo0cmV2N2N4Y2QzOCZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/12jpDs6Z9rSQNO/giphy.gif",
}

# Store messages
message_log = []

async def handle_message(update: Update, context: CallbackContext) -> None:
    """
    Process incoming messages and respond with a sticker, emoji or GIF based on triggers.

    Logs the message with a timestamp, then checks for any sticker or emoji triggers.
    If a sticker trigger is found, sends the corresponding sticker and stops further processing.
    Otherwise, checks for emoji triggers and reacts to the first match found.
    """
    message_text = update.message.text.lower()
    chat_id = update.message.chat_id

    # Log message with timestamp
    message_log.append((datetime.utcnow(), chat_id, update.message.text))

    # Check for GIF triggers
    for keyword, gif_url in GIFS.items():
        if keyword in message_text:
            await context.bot.send_animation(chat_id=chat_id, animation=gif_url)
            return

    # Check for sticker triggers
    for keyword, sticker_id in STICKERS.items():
        if keyword in message_text:
            await context.bot.send_sticker(chat_id=chat_id, sticker=sticker_id)
            return

    # Check for emoji triggers
    for keyword, emoji in KEYWORDS.items():
        if keyword in message_text:
            await context.bot.send_message(chat_id=chat_id, text=emoji)
            return
