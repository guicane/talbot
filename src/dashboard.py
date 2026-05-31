"""
Streamlit statistics dashboard displaying active chat metrics from SQLite messages database.
"""

import os
import sqlite3
from datetime import datetime
import pandas as pd
import streamlit as st
from message_store import init_db

# Configure page metadata and layout
st.set_page_config(
    page_title="Talbot Bot Statistics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Dark theme visual styling overrides
st.markdown("""
<style>
    .stApp {
        background-color: #0e1117;
        color: #c9d1d9;
    }
    .css-1r6qpt5 {
        background-color: #161b22;
    }
    .metric-card {
        background-color: #1f242c;
        border: 1px solid #30363d;
        border-radius: 8px;
        padding: 15px;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)


def load_data(db_path="messages.db"):
    """
    Query all messages from the SQLite database and load them into a pandas DataFrame.
    """
    # Ensure database and columns are initialized
    init_db()

    if not os.path.exists(db_path):
        return pd.DataFrame()

    conn = None
    try:
        conn = sqlite3.connect(db_path)
        query = "SELECT chat_id, user_id, message, timestamp, chat_title, user_name FROM messages"
        df = pd.read_sql_query(query, conn)
        return df
    except sqlite3.Error as e:
        st.error(f"Database read error: {e}")
        return pd.DataFrame()
    finally:
        if conn:
            conn.close()


# Sidebar controls
st.sidebar.title("⚙️ Talbot Control Panel")
st.sidebar.markdown("---")

# Data Refresh controls
st.sidebar.subheader("🔄 Data Polling")
auto_refresh = st.sidebar.checkbox("Real-time Auto-refresh (10s)", value=False)

if st.sidebar.button("Fetch Fresh Data"):
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.info(
    "📊 **Talbot Statistics Dashboard** displays active group chat metrics, "
    "message volume distributions, and user activity metrics in real-time."
)

# Load the SQLite database
df_messages = load_data()

# Header Layout
st.title("📊 Talbot Bot Group Chat Statistics")
st.subheader("Real-time telemetry and message analytics dashboard")
st.markdown("---")

if df_messages.empty:
    st.warning("⚠️ No message data found. Verify that the messages.db database exists and contains records.")
else:
    # Pre-process dates
    df_messages['datetime'] = pd.to_datetime(df_messages['timestamp'], unit='s')
    df_messages['hour'] = df_messages['datetime'].dt.hour
    df_messages['date_hour'] = df_messages['datetime'].dt.strftime('%Y-%m-%d %H:00')

    # Handle missing or null chat titles and user names for backward compatibility
    df_messages['chat_display'] = df_messages['chat_title'].fillna('').astype(str)
    df_messages.loc[df_messages['chat_display'].str.strip() == '', 'chat_display'] = \
        df_messages['chat_id'].astype(str)

    df_messages['user_display'] = df_messages['user_name'].fillna('').astype(str)
    df_messages.loc[df_messages['user_display'].str.strip() == '', 'user_display'] = \
        df_messages['user_id'].astype(str)

    # Build unique chats mapping for the sidebar selectbox
    chat_mapping = df_messages.groupby('chat_id')['chat_display'].first().to_dict()
    sorted_chat_ids = sorted(chat_mapping.keys(), key=lambda cid: chat_mapping[cid].lower())

    st.sidebar.markdown("---")
    st.sidebar.subheader("💬 Select Group Chat")

    chat_options = ["Global"] + sorted_chat_ids

    def format_chat(chat_val):
        """Format helper to show display name instead of ID in selectbox."""
        if chat_val == "Global":
            return "Global (All Chats)"
        return chat_mapping.get(chat_val, str(chat_val))

    selected_chat = st.sidebar.selectbox(
        "Filter stats by chat:",
        options=chat_options,
        format_func=format_chat
    )

    # Filter dataset based on selection
    if selected_chat != "Global":
        df_filtered = df_messages[df_messages['chat_id'] == selected_chat]
    else:
        df_filtered = df_messages

    # Metric Row
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(label="💬 Total Messages Logged", value=len(df_filtered))
    with col2:
        st.metric(label="👥 Unique Active Chats", value=df_filtered['chat_id'].nunique())
    with col3:
        st.metric(label="👤 Unique Active Users", value=df_filtered['user_id'].nunique())
    with col4:
        avg_len = df_filtered['message'].str.len().mean()
        avg_len_val = f"{avg_len:.1f} chars" if not pd.isna(avg_len) else "0.0 chars"
        st.metric(label="📝 Avg Message Length", value=avg_len_val)

    st.markdown("---")

    # Visualizations Row 1
    left_col, right_col = st.columns(2)

    with left_col:
        st.subheader("📈 Message Distribution per Group Chat")
        # Count messages per chat using beautiful display names
        chat_counts = df_filtered['chat_display'].value_counts().reset_index()
        chat_counts.columns = ['Chat Group', 'Message Count']
        st.bar_chart(chat_counts.set_index('Chat Group'))

    with right_col:
        st.subheader("🥇 Top Active Users (Most Talkative)")
        # Count messages per user using beautiful display names
        user_counts = df_filtered['user_display'].value_counts().head(10).reset_index()
        user_counts.columns = ['User', 'Message Count']
        st.bar_chart(user_counts.set_index('User'))

    st.markdown("---")

    # Visualizations Row 2
    st.subheader("⏱️ Hourly Message Count Distribution (Daily Activity)")
    hour_counts = df_filtered['hour'].value_counts().reindex(range(24), fill_value=0).reset_index()
    hour_counts.columns = ['Hour of Day (24h)', 'Message Count']
    st.area_chart(hour_counts.set_index('Hour of Day (24h)'))

    # Footer/Status message
    st.markdown("---")
    st.caption(
        f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | "
        "Talbot statistics are parsed dynamically from sqlite context."
    )

# Handle Auto-refresh logic at the end of the script
if auto_refresh:
    import time
    time.sleep(10)
    st.rerun()
