"""
This module contains the logic to fetch and summarize messages from the last 24 hours for each chat.
"""
import time
import sqlite3
import asyncio
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer, pipeline, logging
import torch

# Silence Hugging Face warning/verbosity logs
logging.set_verbosity_error()

MODEL_NAME = "facebook/bart-large-cnn"
summarizer = None  # pylint: disable=invalid-name

def get_summarizer():
    """Lazy-load the summarizer model."""
    # pylint: disable=global-statement, invalid-name
    global summarizer
    if summarizer is None:
        print("[DEBUG] Loading Summarization Model...")
        # Detect if GPU is available (MPS for Mac, CUDA for NVIDIA, fallback to CPU)
        DEVICE = "mps" if torch.backends.mps.is_available() else "cpu"
        print(f"[DEBUG] Using device: {DEVICE}")
        try:
            tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
            model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_NAME).to(DEVICE)
            summarizer = pipeline("summarization", model=model, tokenizer=tokenizer, device=0 if DEVICE != "cpu" else -1)
            print("[DEBUG] Summarization Model Loaded Successfully!")
        except OSError as e:
            print(f"[ERROR] Model loading failed (File issue): {e}")
            return None
        except ValueError as e:
            print(f"[ERROR] Model configuration issue: {e}")
            return None
        except Exception as e:  # pylint: disable=broad-exception-caught
            print(f"[ERROR] General error loading model: {e}")
            return None
    return summarizer

def summarize_messages(messages):
    """Summarizes a list of messages using bart-large-cnn."""
    if not messages:
        print("[DEBUG] No messages found for summarization.")
        return "No messages found in the selected timeframe."

    input_text = " ".join(messages)[:1024]  # ✅ Limit input to avoid errors
    print(f"[DEBUG] Generating summary for {len(messages)} messages...")

    # Load summarizer on demand
    sum_pipeline = get_summarizer()
    if sum_pipeline is None:
        return "Error: Summarization model could not be loaded."

    try:
        response = sum_pipeline(input_text, max_length=100, min_length=20, do_sample=False)
        summary = response[0]["summary_text"]
        print(f"[DEBUG] Summary Generated: {summary}")
        return summary
    except IndexError:
        print("[ERROR] Model returned an unexpected empty response.")
        return "Error: Model failed to generate a summary."
    except RuntimeError as e:
        print(f"[ERROR] Runtime error (likely due to memory): {e}")
        return "Error: Model ran out of memory."
    except ValueError as e:
        print(f"[ERROR] Invalid input data: {e}")
        return "Error: Invalid input for summarization."

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
    except sqlite3.DatabaseError as e:
        print(f"[ERROR] General database error: {e}")
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
        summary_text = await asyncio.to_thread(summarize_messages, messages)

        if summary_text:
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"📌 *Daily Summary for Today:* 📌\n\n{summary_text}",
                parse_mode="Markdown"
            )
