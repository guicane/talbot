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
    log_dir = "/app/logs"
    #log_file = os.path.join(log_dir, "bot_debug.log")

    # Ensure the log directory exists
    os.makedirs(log_dir, exist_ok=True)

    #def setup_logging_config():
    #    logging.basicConfig(
    #        level=logging.INFO,
    #        format="%(asctime)s - %(levelname)s - %(message)s",
    #        handlers=[
    #            logging.FileHandler(log_file),
    #            logging.StreamHandler()
    #        ]
    #    )

    # Check if the root logger already has handlers to avoid adding duplicate ones
    if not logging.getLogger().hasHandlers():
        logging.basicConfig(
            format="%(asctime)s - %(levelname)s - [%(name)s] %(message)s",
            level=logging.INFO,
            handlers=[
                logging.FileHandler(os.path.join(log_dir, "bot_debug.log")),
                logging.StreamHandler(),
            ]
        )
