"""
Module for handling insult commands using the Evil Insult API.
"""

import requests
from telegram.ext import CommandHandler

def fetch_insult() -> str:
    """
    Fetch an insult from the Evil Insult API.

    :return: A string containing the insult.
    """
    url = "https://evilinsult.com/generate_insult.php?lang=en&type=text"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return response.text.strip()
        return "I ran out of insults, but just imagine something mean!"
    except requests.RequestException as exc:
        return "Error retrieving insult, please try again later. ({exc})"


async def insult_command(update, context):
    """
    Handle the /insult command by fetching an insult and sending it to the chat.

    :param update: Telegram update object.
    :param context: Telegram context object.
    """
    if not context.args:
        print("No user specified for /insult command")
        await context.bot.send_message(
            chat_id=update.message.chat_id, text="Usage: /insult @username"
        )
        return

    user_to_insult = " ".join(context.args)
    insult = fetch_insult()
    message = f"Hey {user_to_insult}, {insult[:1].lower() + insult[1:]}"
    await context.bot.send_message(chat_id=update.message.chat_id, text=message)


def register_insult_handler(app):
    """
    Register the /insult command handler with the Telegram application.

    :param app: The Telegram application instance.
    """
    print("Registering /insult command handler")
    app.add_handler(CommandHandler("insult", insult_command))
