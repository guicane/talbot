"""
Module for handling the /brl command, which shows the current GBP to BRL conversion rate.
"""

from datetime import datetime
import os
import asyncio
import requests
from telegram import Update
from telegram.ext import CommandHandler, CallbackContext


def get_gbp_brl_rate() -> str:
    """
    Fetch the latest conversion rate from GBP to BRL using exchangerate.host API.

    :return: A formatted string with the conversion rate or an error message.
    """

    try:
        api_key = os.getenv("EXCHANGERATE_API_KEY", "275a69f308281c5d123e7b11b76a795a")
        url = f"https://api.exchangerate.host/live?access_key={api_key}"
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
        print("Invalid response format from exchange rate API: %s", data)
        return "Unable to retrieve conversion rate at this time."
    except requests.RequestException as exc:
        print("Error fetching GBP to BRL rate: %s", exc)
        return "Error retrieving conversion rate. Please try again later."


async def brl_command(update: Update, context: CallbackContext) -> None:
    """
    Handle the /brl command by fetching the GBP to BRL conversion rate and sending it to the chat.

    :param update: Telegram update object.
    :param context: Telegram context object.
    """
    print("Received /brl command from user %s", update.message.from_user.id)
    conversion_message = await asyncio.to_thread(get_gbp_brl_rate)
    await context.bot.send_message(
        chat_id=update.message.chat_id, text=conversion_message
    )


def get_btc_usd_price() -> str:
    """
    Fetch the latest BTC/USD price from AwesomeAPI.

    :return: A formatted string with the current BTC price or an error message.
    """
    try:
        url = "https://economia.awesomeapi.com.br/json/last/BTC-USD"
        response = requests.get(url, timeout=10)
        data = response.json()

        if response.status_code == 200 and "BTCUSD" in data:
            price = float(data["BTCUSD"]["bid"])
            timestamp = int(data["BTCUSD"]["timestamp"])
            last_update = datetime.utcfromtimestamp(timestamp)
            last_updated_formatted = last_update.strftime("%y-%m-%d %H:%M")

            return f"1 BTC = ${price:,.2f} USD\n({last_updated_formatted})"
        print("Invalid response format from BTC price API: %s", data)
        return "Unable to retrieve Bitcoin price at this time."
    except requests.RequestException as exc:
        print("Error fetching BTC price: %s", exc)
        return "Error retrieving Bitcoin price. Please try again later."


async def btc_command(update: Update, context: CallbackContext) -> None:
    """
    Handle the /btc command by fetching the BTC to USD rate and sending it to the chat.
    """
    print("Received /btc command from user %s", update.message.from_user.id)
    btc_message = await asyncio.to_thread(get_btc_usd_price)
    await context.bot.send_message(
        chat_id=update.message.chat_id, text=btc_message
    )


def register_brl_handler(app) -> None:
    """
    Register the /brl and /btc command handlers with the Telegram application.

    :param app: The Telegram application instance.
    """
    print("Registering /brl and /btc command handlers")
    app.add_handler(CommandHandler("brl", brl_command))
    app.add_handler(CommandHandler("btc", btc_command))
