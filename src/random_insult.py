from telegram.ext import CallbackContext, CommandHandler
import logging
import requests

# Enable logging to file with script name as prefix
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - [InsultBot] %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler("bot_debug.log"),  # Log to a file
        logging.StreamHandler()  # Log to console as well
    ]
)
logger = logging.getLogger(__name__)

# Function to fetch an insult from Evil Insult API
def fetch_insult() -> str:
    url = "https://evilinsult.com/generate_insult.php?lang=en&type=text"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return response.text.strip()
        else:
            logger.warning("Failed to fetch insult from Evil Insult API")
            return "I ran out of insults, but just imagine something mean!"
    except requests.RequestException as e:
        logger.error(f"Error fetching insult: {e}")
        return "Error retrieving insult, please try again later."

# Telegram command handler for insults
async def insult_command(update, context):
    logger.info(f"Received /insult command from user {update.message.from_user.id}")
    
    if not context.args:
        logger.warning("No user specified for /insult command")
        await context.bot.send_message(chat_id=update.message.chat_id, text="Usage: /insult @username")
        return
    
    user_to_insult = " ".join(context.args)
    insult = fetch_insult()
    message = f"{user_to_insult}, {insult}"
    
    logger.info(f"Sending insult: {message}")
    await context.bot.send_message(chat_id=update.message.chat_id, text=message)

# Function to register the /insult command
def register_insult_handler(app):
    logger.info("Registering /insult command handler")
    app.add_handler(CommandHandler("insult", insult_command))
