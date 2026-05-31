"""
Module to store incoming messages in a SQLite database and purge old messages.
"""
import sqlite3
import time

DB_FILE = "messages.db"

def init_db():
    """Initialize the database and handle schema migrations."""
    conn = None
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER,
                user_id INTEGER,
                message TEXT,
                timestamp INTEGER
            )
        ''')

        # Schema migration: Check if chat_title and user_name columns exist
        cursor.execute("PRAGMA table_info(messages)")
        columns = [column[1] for column in cursor.fetchall()]
        if "chat_title" not in columns:
            cursor.execute("ALTER TABLE messages ADD COLUMN chat_title TEXT")
        if "user_name" not in columns:
            cursor.execute("ALTER TABLE messages ADD COLUMN user_name TEXT")

        conn.commit()
        conn.close()
        print("✅ Database initialized and schema migrations verified!")

    except sqlite3.OperationalError as e:
        print(f"[ERROR] Database operation failed: {e}")
    except sqlite3.DatabaseError as e:
        print(f"[ERROR] General database error: {e}")
    finally:
        if conn:
            conn.close()

def store_message(chat_id, user_id, message, chat_title=None, user_name=None):
    """Store incoming messages in the database with metadata."""
    timestamp = int(time.time())
    conn = None

    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO messages (chat_id, user_id, message, timestamp, chat_title, user_name) VALUES (?, ?, ?, ?, ?, ?)",
            (chat_id, user_id, message, timestamp, chat_title, user_name)
        )
        conn.commit()
        conn.close()

        print(f"✅ [DB] Stored message: Chat={chat_id} ({chat_title}), User={user_id} ({user_name}), Message={message}")

    except sqlite3.OperationalError as e:
        print(f"[ERROR] Database operation failed: {e}")
    except sqlite3.IntegrityError as e:
        print(f"[ERROR] Data integrity issue: {e}")
    except sqlite3.DatabaseError as e:
        print(f"[ERROR] General database error: {e}")
    finally:
        if conn:
            conn.close()

async def purge_old_messages(_):
    """Delete messages older than 24 hours."""
    cutoff_time = int(time.time()) - 86400  # 24 hours ago
    conn = None
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM messages WHERE timestamp < ?", (cutoff_time,))
        conn.commit()
        print("[DEBUG] Old messages purged.")

    except sqlite3.OperationalError as e:
        print(f"[ERROR] Database operation failed: {e}")
    except sqlite3.DatabaseError as e:
        print(f"[ERROR] General database error: {e}")
    finally:
        if conn:
            conn.close()

init_db()
print("[DB] Initialized database and ensured messages table exists.")
