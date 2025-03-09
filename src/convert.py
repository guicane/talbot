"""
Module for handling the /brl command, which shows the current GBP to BRL conversion rate.
"""

import logging
from datetime import datetime
import requests
from telegram import Update
from telegram.ext import CommandHandler, CallbackContext

# Get the module-specific logger
logger = logging.getLogger(__name__)


def get_gbp_brl_rate() -> str:
    """
    Fetch the latest conversion rate from GBP to BRL using exchangerate.host API.

    :return: A formatted string with the conversion rate or an error message.
    """

    try:
        url = "https://api.exchangerate.host/live?access_key=275a69f308281c5d123e7b11b76a795a"
        params = {
            "source": "GBP",
            "quotes": "GBPBRL"
        }

        response = requests.get(url, params=params, timeout=10)
        data = response.json()

        if response.status_code == 200 and "GBPBRL" in data["quotes"]:
            rate = data["quotes"]["GBPBRL"]
            last_update = datetime.utcfromtimestamp(data["timestamp"])
            last_updated_formatted = last_update.strftime("%y-%m-%d %H:%M")

            return f"1 GBP = {rate:.4f} BRL\n({last_updated_formatted})"
        logger.error("Invalid response format from exchange rate API: %s", data)
        return "Unable to retrieve conversion rate at this time."
    except requests.RequestException as exc:
        logger.error("Error fetching GBP to BRL rate: %s", exc)
        return "Error retrieving conversion rate. Please try again later."


async def brl_command(update: Update, context: CallbackContext) -> None:
    """
    Handle the /brl command by fetching the GBP to BRL conversion rate and sending it to the chat.

    :param update: Telegram update object.
    :param context: Telegram context object.
    """
    logger.info("Received /brl command from user %s", update.message.from_user.id)
    conversion_message = get_gbp_brl_rate()
    await context.bot.send_message(
        chat_id=update.message.chat_id, text=conversion_message
    )


def register_brl_handler(app) -> None:
    """
    Register the /brl command handler with the Telegram application.

    :param app: The Telegram application instance.
    """
    logger.info("Registering /brl command handler")
    app.add_handler(CommandHandler("brl", brl_command))
