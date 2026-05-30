"""
Module for handling Telegram messages by reacting with emojis or stickers.
"""
import time
import datetime
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

def get_timeframe_range(selected_option):
    """Calculate start_time and end_time for a given selected_option."""
    now = int(time.time())
    if selected_option in SUMMARY_OPTIONS:
        timeframe = SUMMARY_OPTIONS[selected_option]
        return now - timeframe, None
    if selected_option == "today":
        now_dt = datetime.datetime.now()
        today_midnight = datetime.datetime(now_dt.year, now_dt.month, now_dt.day)
        return int(today_midnight.timestamp()), None
    if selected_option == "yesterday":
        now_dt = datetime.datetime.now()
        today_midnight = datetime.datetime(now_dt.year, now_dt.month, now_dt.day)
        yesterday_midnight = today_midnight - datetime.timedelta(days=1)
        return int(yesterday_midnight.timestamp()), int(today_midnight.timestamp())
    return None, None

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

async def summary_command(update: Update, context: CallbackContext):
    """Send private inline keyboard or directly generate summary if argument provided."""
    try:
        user_id = update.message.from_user.id
        chat_id = update.message.chat_id
        print(f"Received /summary command from user {user_id}")

        # Check if an argument is provided (e.g. /summary 1h)
        if context.args:
            selected_option = context.args[0].lower()
            if selected_option in SUMMARY_OPTIONS or selected_option in ["today", "yesterday"]:
                time_range = get_timeframe_range(selected_option)

                # Try to delete the user's command message to keep group clean
                try:
                    await update.message.delete()
                except Exception:  # pylint: disable=broad-exception-caught
                    pass

                print(f"[DEBUG] Direct fetch: Fetching messages for {selected_option}...")
                messages = fetch_messages(chat_id, time_range[0], time_range[1])
                summary = await asyncio.to_thread(summarize_messages, chat_id, messages)

                if selected_option in ["today", "yesterday"]:
                    header = f"📌 *Summary for {selected_option}:*\n\n"
                else:
                    header = f"📌 *Summary for the last {selected_option}:*\n\n"

                # Send directly to private chat
                try:
                    await context.bot.send_message(
                        chat_id=user_id,
                        text=f"{header}{summary}",
                        parse_mode="Markdown"
                    )
                except TelegramError as err:
                    if "Forbidden" in str(err) or "conversation" in str(err):
                        bot_info = await context.bot.get_me()
                        user = update.message.from_user
                        mention = f"@{user.username}" if user.username else user.first_name
                        await context.bot.send_message(
                            chat_id=chat_id,
                            text=f"⚠️ {mention}, I cannot send you a private message. "
                                 f"Please click @{bot_info.username} and press **Start** first, then try again!"
                        )
                        return
                    raise err
                return

            await update.message.reply_text(
                f"❌ Invalid timeframe. Supported options: today, yesterday, {', '.join(SUMMARY_OPTIONS.keys())}"
            )
            return

        # Fallback: Send inline keyboard
        keyboard = [
            [
                InlineKeyboardButton("Today's Summary", callback_data="today"),
                InlineKeyboardButton("Yesterday's Summary", callback_data="yesterday")
            ]
        ] + [[InlineKeyboardButton(f"{key} Summary", callback_data=key)] for key in SUMMARY_OPTIONS]

        await update.message.reply_text(
            "Select the time range for the summary:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    except (TelegramError, AttributeError) as err:
        print(f"[ERROR] Exception during summary command: {err}")

async def handle_summary_selection(update: Update, context: CallbackContext):
    """Fetch and summarize messages based on user selection."""
    try:
        query = update.callback_query
        await query.answer()

        user_id = query.from_user.id
        chat_id = query.message.chat_id
        selected_option = query.data  # Get selected timeframe (e.g., "1h", "today")

        print(f"[DEBUG] User {user_id} selected: {selected_option}")

        if selected_option not in SUMMARY_OPTIONS and selected_option not in ["today", "yesterday"]:
            print(f"[ERROR] Invalid selection: {selected_option}")
            await query.message.reply_text("❌ Invalid selection. Please try again.")
            return

        time_range = get_timeframe_range(selected_option)

        print(f"[DEBUG] Fetching messages for {selected_option}...")

        messages = fetch_messages(chat_id, time_range[0], time_range[1])

        print(f"[DEBUG] Retrieved {len(messages)} messages.")

        summary = await asyncio.to_thread(summarize_messages, chat_id, messages)

        print(f"[DEBUG] Sending summary to user {user_id}.")

        if selected_option in ["today", "yesterday"]:
            header = f"📌 *Summary for {selected_option}:*\n\n"
        else:
            header = f"📌 *Summary for the last {selected_option}:*\n\n"

        try:
            await context.bot.send_message(
                chat_id=user_id,  # Send summary in private chat
                text=f"{header}{summary}",
                parse_mode="Markdown"
            )
        except TelegramError as err:
            if "Forbidden" in str(err) or "conversation" in str(err):
                bot_info = await context.bot.get_me()
                mention = f"@{query.from_user.username}" if query.from_user.username else query.from_user.first_name
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=f"⚠️ {mention}, I cannot send you a private message. "
                         f"Please click @{bot_info.username} and press **Start** first, then try again!"
                )
                return
            raise err

        # Delete the inline keyboard menu message to keep the group chat clean
        try:
            await query.message.delete()
        except Exception as e:  # pylint: disable=broad-exception-caught
            print(f"[DEBUG] Could not delete inline menu message: {e}")

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
