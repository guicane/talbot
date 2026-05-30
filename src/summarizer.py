"""
This module contains the logic to fetch and summarize messages from the last 24 hours for each chat
using the serverless Google Gemini 2.5 Flash API with built-in rate limits to prevent billing.
"""
import time
import sqlite3
import os
import asyncio
import requests

API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"

# Cooldown and Rate Limit parameters
COOLDOWN_SECONDS = 300  # 5 minutes cooldown per chat/group
DAILY_LIMIT = 50       # Strict global cap of 50 requests per day bot-wide

# In-memory rate limiting state
_last_request_time = {}
_daily_requests = {
    "date": "",
    "count": 0
}

def summarize_messages(chat_id, messages):
    """Summarizes a list of messages using the serverless Gemini 2.5 Flash API."""
    # pylint: disable=too-many-locals, too-many-return-statements
    if not messages:
        print(f"[DEBUG] No messages found for chat {chat_id} summarization.")
        return "No messages found in the selected timeframe."

    # 1. Enforce Bot-Wide Daily Cap (Billing protection)
    current_date = time.strftime("%Y-%m-%d")
    if _daily_requests["date"] != current_date:
        _daily_requests["date"] = current_date
        _daily_requests["count"] = 0

    if _daily_requests["count"] >= DAILY_LIMIT:
        print(f"[WARNING] Daily global summary limit reached ({DAILY_LIMIT} requests). Request blocked.")
        return "Error: The daily global bot summary limit has been reached to protect against API billing. Please try again tomorrow."

    # 2. Enforce Chat-Level Cooldown (Spam protection)
    now = time.time()
    last_time = _last_request_time.get(chat_id, 0)
    if now - last_time < COOLDOWN_SECONDS:
        remaining = int(COOLDOWN_SECONDS - (now - last_time))
        print(f"[WARNING] Chat {chat_id} requested summary too soon. Cooldown active. Remaining: {remaining}s.")
        return f"Error: Cooldown active. Please wait {remaining} seconds before requesting another summary in this chat."

    # 3. Retrieve Gemini API Key
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("[ERROR] GEMINI_API_KEY environment variable is not set!")
        return "Error: Gemini API Key is missing. Please set the GEMINI_API_KEY environment variable in the bot settings."

    # Update rate limits (only after validating API key exists)
    _last_request_time[chat_id] = now
    _daily_requests["count"] += 1
    print(f"[DEBUG] Processing summary request {_daily_requests['count']}/{DAILY_LIMIT} today for chat {chat_id}...")

    # Format the chat logs for the prompt
    chat_log = "\n".join(messages)[:12000]  # Limit context window to 12k chars for security/safety

    prompt = (
        "You are Talbot, a helpful and humorous group chat assistant. "
        "Your task is to summarize the following chat logs into a well-structured, easy-to-read digest. "
        "Identify each individual discussion topic or thread in the chat, and emphasize each topic individually. "
        "Under each topic, use detailed bullet points to list key arguments, main participants, decisions made, "
        "and any interesting or funny moments related specifically to that topic. "
        "Use appropriate emojis for each section to make it engaging. "
        "Keep the summary direct. Do not include any meta-introductions (like 'Here is the summary:'). "
        "Here are the chat logs:\n\n"
        f"{chat_log}"
    )

    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": prompt
                    }
                ]
            }
        ]
    }

    headers = {
        "Content-Type": "application/json"
    }

    try:
        url = f"{API_URL}?key={api_key}"
        response = requests.post(url, headers=headers, json=payload, timeout=25)

        # Handle Rate Limits (Gemini free tier allows 15 RPM)
        if response.status_code == 429:
            print("[ERROR] Gemini API returned 429 (Rate Limit Exceeded).")
            return "Error: Google AI Studio free tier rate limit exceeded. Please wait a minute and try again."

        response.raise_for_status()
        data = response.json()

        if "candidates" in data and len(data["candidates"]) > 0:
            candidate = data["candidates"][0]
            if "content" in candidate and "parts" in candidate["content"] and len(candidate["content"]["parts"]) > 0:
                summary = candidate["content"]["parts"][0]["text"].strip()
                # Escape legacy markdown characters (like stray _ and [) to prevent Telegram parsing crashes
                safe_summary = summary.replace("_", "\\_").replace("[", "\\[")
                print(f"[DEBUG] Gemini Summary Generated: {len(safe_summary)} characters.")
                return safe_summary

        print(f"[ERROR] Unexpected Gemini API response format: {data}")
        return "Error: Summarization service returned an unexpected response."

    except requests.RequestException as e:
        print(f"[ERROR] Gemini API request failed: {e}")
        return "Error: Failed to connect to the Google summarization service. Please try again later."
    except Exception as e:  # pylint: disable=broad-exception-caught
        print(f"[ERROR] Unexpected exception during summarization: {e}")
        return "Error: Summarization failed due to an unexpected internal error."

def fetch_messages(chat_id, start_time):
    """Retrieve messages from the last X hours."""
    print(f"[DEBUG] Fetching messages for chat {chat_id} from timestamp {start_time}...")

    conn = sqlite3.connect("messages.db")
    cursor = conn.cursor()

    try:
        cursor.execute(
            "SELECT message FROM messages WHERE chat_id = ? AND timestamp >= ?", 
            (chat_id, start_time)
        )
        messages = [row[0] for row in cursor.fetchall()]
        print(f"[DEBUG] Retrieved {len(messages)} messages from DB.")
    except sqlite3.OperationalError as e:
        print(f"[ERROR] Database operation failed: {e}")
        messages = []
    except sqlite3.DatabaseError as e:
        print(f"[ERROR] General database error: {e}")
        messages = []
    finally:
        if conn:
            conn.close()

    return messages

async def daily_group_summary(context):
    """Fetch and summarize messages from the last 24h for each chat and post in the group."""
    conn = sqlite3.connect("messages.db")
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT chat_id FROM messages")
    chat_ids = [row[0] for row in cursor.fetchall()]
    conn.close()

    now = int(time.time())
    start_time = now - 86400  # 24 hours ago

    for chat_id in chat_ids:
        messages = fetch_messages(chat_id, start_time)
        # Pass chat_id to enforce rate limits
        summary_text = await asyncio.to_thread(summarize_messages, chat_id, messages)

        if summary_text:
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"📌 *Daily Summary for Today:* 📌\n\n{summary_text}",
                parse_mode="Markdown"
            )
