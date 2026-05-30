#!/bin/bash

echo "[SUPERVISOR] Starting Streamlit statistics dashboard on port 8501..."
streamlit run dashboard.py --server.port 8501 --server.address 0.0.0.0 &
STREAMLIT_PID=$!

echo "[SUPERVISOR] Starting Telegram Talbot Bot..."
python bot.py &
BOT_PID=$!

# Monitor background processes. Exit immediately if either exits
wait -n

echo "[SUPERVISOR] A background process exited. Shutting down container..."
kill $STREAMLIT_PID 2>/dev/null
kill $BOT_PID 2>/dev/null
exit 1
