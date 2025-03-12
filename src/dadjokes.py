"""
Module for interacting with the Dad Jokes API and pulling Dad Jokes using the /dadjokes command for Telegram.
"""

import logging
import requests
from telegram import Update
from telegram.ext import CommandHandler, CallbackContext

# Get the module-specific logger
logger = logging.getLogger(__name__)

# Function to fetch a random dad joke
def get_dad_joke() -> str:
    """
    Fetch dad joke from API
    """
    url = "https://icanhazdadjoke.com/"
    headers = {"Accept": "application/json"}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        data = response.json()
        return data.get("joke", "Couldn't fetch a dad joke. Try again!")
    except requests.RequestException as get_joke_error:
        logger.error("Error fetching dad joke: %s", {get_joke_error})
        return "Error retrieving a dad joke. Please try again later."

# Telegram command handler for /dadjokes
async def dadjokes_command(update: Update, context: CallbackContext) -> None:
    """
    Handle the /dadjokes command for Telegram.
    """
    logger.info("Received /dadjokes command from user %s", {update.message.from_user.id})
    chat_id = update.message.chat_id

    if context.args:
        # User provided their own joke
        joke = " ".join(context.args)
    else:
        # Fetch a random joke from the API
        joke = get_dad_joke()

    # Send the joke
    await context.bot.send_message(chat_id=chat_id, text=joke)

    # Create a poll for rating the joke
    poll_options = ["😂 Hilarious", "😆 Good", "😐 Meh", "🙄 Bad", "🤦 Terrible"]
    await context.bot.send_poll(
        chat_id=chat_id,
        question="Rate the previous dad joke",
        options=poll_options,
        is_anonymous=False,
        allows_multiple_answers=False
    )

# Function to register the /dadjokes command
def register_dadjokes_handler(app):
    """
    Register the /dadjokes command and its callback query handler with the Telegram application.
    """
    logger.info("Registering /dadjokes command handler")
    app.add_handler(CommandHandler("dadjokes", dadjokes_command))
