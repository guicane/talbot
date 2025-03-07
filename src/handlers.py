from telegram import Update
from telegram.ext import CallbackContext
import logging
from datetime import datetime

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - [Handlers] %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler("bot_debug.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Define keyword-emoji mapping
KEYWORDS = {
    "cunts": "🍑",
}

# Custom sticker mapping
STICKERS = {
    "not worthwhile": "CAACAgQAAxkBAAEN7OJnw47vgltrMdG3wA9dbm8P-Gq36gACPA0AAscocVEUPP2IDSRDKDYE"  # Replace with actual sticker ID
}

# Store messages
message_log = []

# Function to handle messages and react with emojis or stickers
async def handle_message(update: Update, context: CallbackContext) -> None:
    message_text = update.message.text.lower()
    chat_id = update.message.chat_id
    
    # Log message with timestamp
    message_log.append((datetime.utcnow(), chat_id, update.message.text))
    
    # Check for sticker triggers
    for keyword, sticker_id in STICKERS.items():
        if keyword in message_text:
            await context.bot.send_sticker(chat_id=chat_id, sticker=sticker_id)
            return  # Stop processing after sending a sticker
    
    # Check for emoji triggers
    for keyword, emoji in KEYWORDS.items():
        if keyword in message_text:
            await context.bot.send_message(chat_id=chat_id, text=emoji)
            break  # React to the first keyword found
