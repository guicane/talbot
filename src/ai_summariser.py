from telegram.ext import CallbackContext
import logging
from datetime import datetime, timedelta
import os
import requests
import time

# Enable logging to file with script name as prefix
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - [AI Summariser] %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler("bot_debug.log"),  # Log to a file
        logging.StreamHandler()  # Log to console as well
    ]
)
logger = logging.getLogger(__name__)

# Store messages
message_log = []

# Load Anthropics API key from environment variables
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
if not ANTHROPIC_API_KEY:
    raise ValueError("ANTHROPIC_API_KEY environment variable is not set!")

# Function to summarise messages from the past hour
async def summarise_messages(context: CallbackContext) -> None:
    global message_log  # Declare global at the beginning
    now = datetime.utcnow()
    one_hour_ago = now - timedelta(hours=1)
    
    logger.info("Starting AI summarisation process...")
    
    # Filter messages from the last hour
    recent_messages = [msg for (timestamp, chat_id, msg) in message_log if timestamp >= one_hour_ago]
    
    if not recent_messages or all(msg.strip() == "" for msg in recent_messages):
        logger.info("No messages to summarise in the past hour. Skipping summarisation request.")
        return  # No valid messages to summarise
    
    logger.info(f"Summarising {len(recent_messages)} messages...")
    summary = summarise_text("\n".join(recent_messages))  # Use Claude AI (Anthropic)
    
    # Send summary to each relevant chat
    for chat_id in set(chat_id for (_, chat_id, _) in message_log):
        await context.bot.send_message(chat_id=chat_id, text=f"Summarised conversation of the last hour:\n{summary}")
    
    # Remove old messages
    message_log = [(timestamp, chat_id, msg) for (timestamp, chat_id, msg) in message_log if timestamp >= one_hour_ago]
    logger.info("AI summarisation process completed.")

# AI summarisation function using Anthropic's Claude API
def summarise_text(text: str) -> str:
    url = "https://api.anthropic.com/v1/complete"
    headers = {
        "x-api-key": ANTHROPIC_API_KEY,
        "content-type": "application/json"
    }
    payload = {
        "model": "claude-2.1",  # Change model if needed
        "prompt": f"Summarise the following conversation:\n{text}\n\nProvide a brief and clear summary.",
        "max_tokens": 200,
        "temperature": 0.5
    }
    
    max_retries = 3
    for attempt in range(max_retries):
        logger.info(f"Sending request to AI API (attempt {attempt+1})...")
        response = requests.post(url, json=payload, headers=headers)
        
        if response.status_code == 200:
            logger.info("AI summarisation successful.")
            return response.json().get("completion", "[Summarisation failed]")
        elif response.status_code == 429:
            logger.warning("Rate limit exceeded. Retrying after delay...")
            time.sleep(5 * (attempt + 1))  # Exponential backoff
        else:
            logger.error(f"Error from Anthropics API: {response.text}")
            return "[Summarisation failed]"
    
    logger.error("Max retries reached. AI summarisation unavailable.")
    return "[Rate limit exceeded, summarisation unavailable]"
