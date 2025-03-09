"""
Module for AI summarisation using Anthropic's Claude API.
"""

import logging
import os
import time
from datetime import datetime, timedelta
import requests
from telegram.ext import CallbackContext

# Get the module-specific logger
logger = logging.getLogger(__name__)

# Store messages globally
MESSAGE_LOG = []

# Load Anthropics API key from environment variables
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
if not ANTHROPIC_API_KEY:
    raise ValueError("ANTHROPIC_API_KEY environment variable is not set!")


async def summarise_messages(context: CallbackContext) -> None:
    """
    Summarise messages from the past hour and send the summary to relevant chats.

    This function filters messages from the global MESSAGE_LOG that are less than one hour old,
    sends a summarised conversation to each chat, and removes old messages.
    """
    now = datetime.utcnow()
    one_hour_ago = now - timedelta(hours=1)

    logger.info("Starting AI summarisation process...")

    # Filter messages from the last hour
    recent_messages = [
        msg for (timestamp, chat_id, msg) in MESSAGE_LOG if timestamp >= one_hour_ago
    ]

    if not recent_messages or all(msg.strip() == "" for msg in recent_messages):
        logger.info("No messages to summarise in the past hour. Skipping summarisation request.")
        return  # No valid messages to summarise

    logger.info("Summarising %s messages...", len(recent_messages))
    summary = summarise_text("\n".join(recent_messages))

    # Send summary to each relevant chat
    for chat_id in {chat_id for (_, chat_id, _) in MESSAGE_LOG}:
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"Summarised conversation of the last hour:\n{summary}"
        )

    # Remove old messages
    MESSAGE_LOG[:] = [
        (timestamp, chat_id, msg)
        for (timestamp, chat_id, msg) in MESSAGE_LOG
        if timestamp >= one_hour_ago
    ]

    logger.info("AI summarisation process completed.")


def summarise_text(text: str) -> str:
    """
    Summarise the given text using Anthropic's Claude API.

    :param text: The conversation text to summarise.
    :return: A summary string.
    """
    url = "https://api.anthropic.com/v1/complete"
    headers = {
        "x-api-key": ANTHROPIC_API_KEY,
        "content-type": "application/json",
    }
    payload = {
        "model": "claude-2.1",  # Change model if needed
        "prompt": (
            f"Summarise the following conversation:\n{text}\n\nProvide a brief and clear summary."
        ),
        "max_tokens": 200,
        "temperature": 0.5,
    }

    max_retries = 3
    for attempt in range(max_retries):
        logger.info("Sending request to AI API (attempt %s)...", attempt + 1)
        response = requests.post(url, json=payload, headers=headers, timeout=10)

        if response.status_code == 200:
            logger.info("AI summarisation successful.")
            return response.json().get("completion", "[Summarisation failed]")
        if response.status_code == 429:
            logger.warning("Rate limit exceeded. Retrying after delay...")
            time.sleep(5 * (attempt + 1))  # Exponential backoff
        else:
            logger.error("Error from Anthropics API: %s", response.text)
            return "[Summarisation failed]"

    logger.error("Max retries reached. AI summarisation unavailable.")
    return "[Rate limit exceeded, summarisation unavailable]"
