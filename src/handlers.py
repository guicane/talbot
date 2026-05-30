"""
Module for handling Telegram messages by reacting with emojis or stickers.
"""
import time
import sqlite3
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext
from telegram.error import TelegramError
from requests.exceptions import RequestException
from message_store import store_message
from summarizer import fetch_messages, summarize_messages

SUMMARY_OPTIONS = {
    "1h": 3600,
    "4h": 14400,
    "6h": 21600,
    "12h": 43200,
    "24h": 86400
}

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


async def summary_command(update: Update, _context: CallbackContext):
    """Send private inline keyboard for summary timeframe selection."""
    try:
        print(f"[DEBUG] User {update.message.from_user.id} requested a summary.")

        keyboard = [[InlineKeyboardButton(f"{key} Summary", callback_data=key)] for key in SUMMARY_OPTIONS]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            "Select the time range for the summary:",
            reply_markup=reply_markup
        )

    except TelegramError as e:
        print(f"[ERROR] Telegram API error: {e}")
    except AttributeError as e:
        print(f"[ERROR] Missing message data: {e}")

async def handle_summary_selection(update: Update, context: CallbackContext):
    """Fetch and summarize messages based on user selection."""
    try:
        query = update.callback_query
        await query.answer()

        user_id = query.from_user.id
        chat_id = query.message.chat_id
        selected_option = query.data  # Get selected timeframe (e.g., "1h", "4h")

        print(f"[DEBUG] User {user_id} selected: {selected_option}")

        if selected_option not in SUMMARY_OPTIONS:
            print(f"[ERROR] Invalid selection: {selected_option}")
            await query.message.reply_text("❌ Invalid selection. Please try again.")
            return

        timeframe = SUMMARY_OPTIONS[selected_option]
        now = int(time.time())
        start_time = now - timeframe

        print(f"[DEBUG] Fetching messages from last {selected_option}...")

        messages = fetch_messages(chat_id, start_time)

        print(f"[DEBUG] Retrieved {len(messages)} messages.")

        summary = await asyncio.to_thread(summarize_messages, chat_id, messages)

        print(f"[DEBUG] Sending summary to user {user_id}.")

        await context.bot.send_message(
            chat_id=user_id,  # Send summary in private chat
            text=f"📌 *Summary for the last {selected_option}:*\n\n{summary}",
            parse_mode="Markdown"
        )

        await query.message.reply_text("✅ Your summary has been sent to you in a private chat!")

    except (sqlite3.OperationalError, sqlite3.DatabaseError) as e:
        print(f"[ERROR] Database error: {e}")
    except TelegramError as e:
        print(f"[ERROR] Telegram API error: {e}")
    except RequestException as e:
        print(f"[ERROR] Network issue: {e}")
    except KeyError as e:
        print(f"[ERROR] Invalid dictionary key: {e}")
    except AttributeError as e:
        print(f"[ERROR] Callback data missing: {e}")

async def handle_message(update: Update, context: CallbackContext) -> None:
    """
    Process incoming messages and respond with a sticker, emoji or GIF based on triggers.

    Logs the message with a timestamp, then checks for any sticker or emoji triggers.
    If a sticker trigger is found, sends the corresponding sticker and stops further processing.
    Otherwise, checks for emoji triggers and reacts to the first match found.
    """
    try:
        if not update.message or not update.message.text:
            print("[BOT] Received non-text message or empty update.")
            return

        message_text = update.message.text
        chat_id = update.message.chat_id
        user_id = update.message.from_user.id

        print(f"✅ [BOT] Received message from {user_id} in chat {chat_id}: {message_text}")

        # ✅ Ensure message is stored
        store_message(chat_id, user_id, message_text)

    except (sqlite3.OperationalError, sqlite3.DatabaseError) as e:
        print(f"[ERROR] Database error: {e}")
    except AttributeError as e:
        print(f"[ERROR] Message object is missing: {e}")

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
