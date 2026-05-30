"""
No-as-a-Service (NaaS) Integration for quirky bot rejections and decision making.
"""

import random
import asyncio
import requests
from telegram import Update
from telegram.ext import CommandHandler, CallbackContext

# Comprehensive fallback list of quirky, multilingual, and stylized "No"s
NO_VARIATIONS = [
    "Nyet! 🙅‍♂️",
    "Nein! 🇩🇪",
    "Não! 🇧🇷",
    "Non! 🇫🇷",
    "Ie! 🇯🇵",
    "Nu! 🇷🇴",
    "Ochi! 🇬🇷",
    "Ne! 🇨🇿",
    "Ei! 🇫🇮",
    "Nej! 🇸🇪",
    "Nope. 🥱",
    "Nah. 🛑",
    "Negative. ⛔",
    "Nooooo. 😱",
    "Not in a million years. 🌌",
    "Dream on. 💤",
    "Forget it. 🗑️",
    "Absolutely not. ❌",
    "No way. 🚧",
    "Computer says no. 💻"
]

def get_no_response() -> str:
    """
    Fetch a random 'No' response from the public NaaS API or a local fallback list.
    """
    url = "https://noaas.org/api"
    try:
        response = requests.get(url, timeout=3)
        if response.status_code == 200:
            data = response.json()
            # If API provides a clean "no" structure
            if "no" in data:
                return f"{data['no'].capitalize()}! 🚫"
    except Exception:  # pylint: disable=broad-exception-caught
        # Fail silently and use the robust local list
        pass
    return random.choice(NO_VARIATIONS)


async def no_command(update: Update, context: CallbackContext) -> None:
    """
    Handle the /no command. If it's a reply to a message, replies to that message.
    Deletes the trigger message to keep the chat clean.
    """
    print(f"Received /no command from user {update.message.from_user.id}")
    no_text = await asyncio.to_thread(get_no_response)

    reply_to_message_id = None
    if update.message.reply_to_message:
        reply_to_message_id = update.message.reply_to_message.message_id

    await context.bot.send_message(
        chat_id=update.message.chat_id,
        text=no_text,
        reply_to_message_id=reply_to_message_id
    )

    try:
        await update.message.delete()
    except Exception:  # pylint: disable=broad-exception-caught
        pass


async def decide_command(update: Update, context: CallbackContext) -> None:
    """
    Handle the /decide command. Heavily biased towards saying "No".
    """
    print(f"Received /decide command from user {update.message.from_user.id}")
    if not context.args:
        await update.message.reply_text(
            "⚠️ Please ask a question for me to decide.\n"
            "Example: /decide should I invest in crypto?"
        )
        return

    question = " ".join(context.args)

    # 90% chance of "No", 10% chance of "Yes"
    if random.random() < 0.90:
        no_text = await asyncio.to_thread(get_no_response)
        response = f"❓ *Question*: {question}\n\n🛑 *Decision*: {no_text}"
    else:
        response = f"❓ *Question*: {question}\n\n✅ *Decision*: Fine, I guess... YES. But don't blame me."

    await update.message.reply_text(response, parse_mode="Markdown")


def register_naas_handlers(app) -> None:
    """
    Register the /no and /decide commands with the Telegram application.
    """
    print("Registering NaaS command handlers")
    app.add_handler(CommandHandler("no", no_command))
    app.add_handler(CommandHandler("decide", decide_command))
