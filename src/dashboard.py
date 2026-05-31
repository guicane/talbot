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

# Premium modern dark theme visual styling overrides
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&display=swap');

    /* Global Typography & Background Override */
    .stApp {
        background-color: #08090d;
        font-family: 'Outfit', -apple-system, BlinkMacSystemFont, sans-serif;
        color: #f0f6fc;
    }

    /* Sidebar Refinements */
    [data-testid="stSidebar"] {
        background-color: #0b0c10 !important;
        border-right: 1px solid rgba(255, 255, 255, 0.05);
    }
    [data-testid="stSidebar"] .stMarkdown h1, 
    [data-testid="stSidebar"] .stMarkdown h2, 
    [data-testid="stSidebar"] .stMarkdown h3 {
        font-family: 'Outfit', sans-serif;
        font-weight: 700;
        background: linear-gradient(135deg, #00f5ff 0%, #8a2be2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    /* Custom Glassmorphic KPI Cards Grid */
    .kpi-container {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 16px;
        margin: 20px 0 30px 0;
    }
    @media (max-width: 1024px) {
        .kpi-container {
            grid-template-columns: repeat(2, 1fr);
        }
    }
    @media (max-width: 640px) {
        .kpi-container {
            grid-template-columns: 1fr;
        }
    }

    .kpi-card {
        background: linear-gradient(135deg, rgba(22, 27, 34, 0.6) 0%, rgba(13, 17, 23, 0.8) 100%);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.25);
        transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
        position: relative;
        overflow: hidden;
    }
    .kpi-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 10px 30px rgba(138, 43, 226, 0.15);
        border-color: rgba(138, 43, 226, 0.35);
    }
    .kpi-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: radial-gradient(circle at 100% 0%, rgba(138, 43, 226, 0.08) 0%, transparent 60%);
        pointer-events: none;
    }
    .kpi-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 8px;
    }
    .kpi-title {
        font-size: 13px;
        font-weight: 500;
        color: #8b949e;
        text-transform: uppercase;
        letter-spacing: 0.8px;
    }
    .kpi-icon {
        font-size: 18px;
        background: rgba(255, 255, 255, 0.04);
        padding: 6px;
        border-radius: 8px;
        border: 1px solid rgba(255, 255, 255, 0.05);
    }
    .kpi-value {
        font-size: 30px;
        font-weight: 700;
        background: linear-gradient(135deg, #ffffff 0%, #d8e2eb 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        letter-spacing: -0.5px;
    }

    /* Wrap Chart Columns in Beautiful Cards */
    .chart-wrapper {
        background: rgba(22, 27, 34, 0.3);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 12px;
        padding: 24px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
        margin-bottom: 25px;
    }
    
    .chart-header {
        font-weight: 600;
        font-size: 18px;
        color: #f0f6fc;
        margin-bottom: 15px;
        display: flex;
        align-items: center;
        gap: 8px;
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
st.markdown("""
<div style="margin-bottom: 30px;">
    <h1 style="font-weight: 800; font-size: 38px; background: linear-gradient(135deg, #ffffff 0%, #8b949e 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 5px;">
        📊 Talbot Bot Analytics
    </h1>
    <p style="font-size: 16px; color: #8b949e; font-weight: 400; margin-top: 0; margin-bottom: 0;">
        Real-time telemetry and group chat message analytics dashboard
    </p>
</div>
""", unsafe_allow_html=True)
st.markdown("---")

if df_messages.empty:
    st.warning("⚠️ No message data found. Verify that the messages.db database exists and contains records.")
else:
    # Pre-process dates
    df_messages['datetime'] = pd.to_datetime(df_messages['timestamp'], unit='s')
    df_messages['hour'] = df_messages['datetime'].dt.hour
    df_messages['date_hour'] = df_messages['datetime'].dt.strftime('%Y-%m-%d %H:00')

    # Propagate known names to historical messages sharing the same ID
    # Step 1: Replace empty or whitespace strings with None/NaN so pandas can handle them
    df_messages['chat_title'] = df_messages['chat_title'].replace(r'^\s*$', pd.NA, regex=True)
    df_messages['user_name'] = df_messages['user_name'].replace(r'^\s*$', pd.NA, regex=True)

    # Step 2: Propagate names within groups sharing the same chat_id / user_id using ffill and bfill
    df_messages['chat_title'] = df_messages.groupby('chat_id')['chat_title'].transform(
        lambda x: x.ffill().bfill()
    )
    df_messages['user_name'] = df_messages.groupby('user_id')['user_name'].transform(
        lambda x: x.ffill().bfill()
    )

    # Step 3: Compute fallback display columns
    df_messages['chat_display'] = df_messages['chat_title'].fillna(df_messages['chat_id'].astype(str))
    df_messages['user_display'] = df_messages['user_name'].fillna(df_messages['user_id'].astype(str))

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

    # Metric Row using Custom Glassmorphic HTML Grid
    total_messages = len(df_filtered)
    unique_chats = df_filtered['chat_id'].nunique()
    unique_users = df_filtered['user_id'].nunique()
    avg_len = df_filtered['message'].str.len().mean()
    avg_len_val = f"{avg_len:.1f} chars" if not pd.isna(avg_len) else "0.0 chars"

    st.markdown(f"""
    <div class="kpi-container">
        <div class="kpi-card">
            <div class="kpi-header">
                <span class="kpi-title">Total Messages</span>
                <span class="kpi-icon">💬</span>
            </div>
            <div class="kpi-value">{total_messages}</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-header">
                <span class="kpi-title">Active Chats</span>
                <span class="kpi-icon">👥</span>
            </div>
            <div class="kpi-value">{unique_chats}</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-header">
                <span class="kpi-title">Active Users</span>
                <span class="kpi-icon">👤</span>
            </div>
            <div class="kpi-value">{unique_users}</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-header">
                <span class="kpi-title">Avg Message Length</span>
                <span class="kpi-icon">📝</span>
            </div>
            <div class="kpi-value" style="font-size: 26px; padding-top: 4px;">{avg_len_val}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # Visualizations Row 1
    left_col, right_col = st.columns(2)

    with left_col:
        st.markdown('<div class="chart-wrapper">', unsafe_allow_html=True)
        st.markdown('<div class="chart-header">📈 Message Distribution per Group Chat</div>', unsafe_allow_html=True)
        # Count messages per chat using beautiful display names
        chat_counts = df_filtered['chat_display'].value_counts().reset_index()
        chat_counts.columns = ['Chat Group', 'Message Count']
        st.bar_chart(chat_counts.set_index('Chat Group'))
        st.markdown('</div>', unsafe_allow_html=True)

    with right_col:
        st.markdown('<div class="chart-wrapper">', unsafe_allow_html=True)
        st.markdown('<div class="chart-header">🥇 Top Active Users (Most Talkative)</div>', unsafe_allow_html=True)
        # Count messages per user using beautiful display names
        user_counts = df_filtered['user_display'].value_counts().head(10).reset_index()
        user_counts.columns = ['User', 'Message Count']
        st.bar_chart(user_counts.set_index('User'))
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("---")

    # Visualizations Row 2
    st.markdown('<div class="chart-wrapper">', unsafe_allow_html=True)
    st.markdown('<div class="chart-header">⏱️ Hourly Message Count Distribution (Daily Activity)</div>', unsafe_allow_html=True)
    hour_counts = df_filtered['hour'].value_counts().reindex(range(24), fill_value=0).reset_index()
    hour_counts.columns = ['Hour of Day (24h)', 'Message Count']
    st.area_chart(hour_counts.set_index('Hour of Day (24h)'))
    st.markdown('</div>', unsafe_allow_html=True)

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
