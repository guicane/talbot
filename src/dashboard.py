"""
Streamlit statistics dashboard displaying active chat metrics from SQLite messages database.
"""

import os
import sqlite3
from datetime import datetime
import pandas as pd
import streamlit as st

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
    if not os.path.exists(db_path):
        return pd.DataFrame()

    conn = None
    try:
        conn = sqlite3.connect(db_path)
        query = "SELECT chat_id, user_id, message, timestamp FROM messages"
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

    # Metric Row
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(label="💬 Total Messages Logged", value=len(df_messages))
    with col2:
        st.metric(label="👥 Unique Active Chats", value=df_messages['chat_id'].nunique())
    with col3:
        st.metric(label="👤 Unique Active Users", value=df_messages['user_id'].nunique())
    with col4:
        avg_len = df_messages['message'].str.len().mean()
        st.metric(label="📝 Avg Message Length", value=f"{avg_len:.1f} chars")

    st.markdown("---")

    # Visualizations Row 1
    left_col, right_col = st.columns(2)

    with left_col:
        st.subheader("📈 Message Distribution per Group Chat")
        # Count messages per chat
        chat_counts = df_messages['chat_id'].value_counts().reset_index()
        chat_counts.columns = ['Chat ID', 'Message Count']
        chat_counts['Chat ID'] = chat_counts['Chat ID'].astype(str)
        st.bar_chart(chat_counts.set_index('Chat ID'))

    with right_col:
        st.subheader("🥇 Top Active Users (Most Talkative)")
        # Count messages per user
        user_counts = df_messages['user_id'].value_counts().head(10).reset_index()
        user_counts.columns = ['User ID', 'Message Count']
        user_counts['User ID'] = user_counts['User ID'].astype(str)
        st.bar_chart(user_counts.set_index('User ID'))

    st.markdown("---")

    # Visualizations Row 2
    st.subheader("⏱️ Hourly Message Count Distribution (Daily Activity)")
    hour_counts = df_messages['hour'].value_counts().reindex(range(24), fill_value=0).reset_index()
    hour_counts.columns = ['Hour of Day (24h)', 'Message Count']
    st.area_chart(hour_counts.set_index('Hour of Day (24h)'))

    # Footer/Status message
    st.markdown("---")
    st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Talbot statistics are parsed dynamically from sqlite context.")

# Handle Auto-refresh logic at the end of the script
if auto_refresh:
    import time
    time.sleep(10)
    st.rerun()
