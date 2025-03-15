"""
Centralized logging configuration for the bot.
"""
import logging
import os

def setup_logging():
    """
    Configures logging for the application.

    This function sets up logging with both a file handler and a stream (console) handler.
    It ensures that all logs include the timestamp, log level, logger name, and message.
    """
    LOG_DIR = "/logs"
    LOG_FILE = os.path.join(LOG_DIR, "bot_debug.log")

    # Ensure the log directory exists
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)

    def setup_logging():
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
            handlers=[
                logging.FileHandler(LOG_FILE),
                logging.StreamHandler()
            ]
        
        )

    # Check if the root logger already has handlers to avoid adding duplicate ones
    if not logging.getLogger().hasHandlers():
        logging.basicConfig(
            format="%(asctime)s - %(levelname)s - [%(name)s] %(message)s",
            level=logging.INFO,
            handlers=[
                logging.FileHandler("../logs/bot_debug.log"),
                logging.StreamHandler(),
            ]
        )
