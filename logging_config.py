"""
Centralized logging configuration for the bot.
"""

import logging

def setup_logging():
    """
    Configures logging for the application.

    This function sets up logging with both a file handler and a stream (console) handler.
    It ensures that all logs include the timestamp, log level, logger name, and message.
    """
    # Check if the root logger already has handlers to avoid adding duplicate ones.
    if not logging.getLogger().hasHandlers():
        logging.basicConfig(
            format="%(asctime)s - %(levelname)s - [%(name)s] %(message)s",
            level=logging.INFO,
            handlers=[
                logging.FileHandler("bot_debug.log"),
                logging.StreamHandler(),
            ]
        )
