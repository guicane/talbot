"""
Lightweight healthcheck script to verify that both the bot and Streamlit are healthy.
"""
import os
import sys
import urllib.request


def check_health() -> bool:
    """
    Check if bot.py is in the process list and Streamlit port 8501 is responsive.
    """
    # 1. Verify that the bot process is running
    pids = [p for p in os.listdir('/proc') if p.isdigit()]
    bot_alive = False

    for pid in pids:
        try:
            with open(f"/proc/{pid}/cmdline", "r", encoding="utf-8") as cmd_file:
                cmd = cmd_file.read()
                if "bot.py" in cmd:
                    bot_alive = True
                    break
        except (IOError, OSError):
            continue

    if not bot_alive:
        print("[HEALTHCHECK] Bot process is not running!")
        return False

    # 2. Verify that the Streamlit web server is responsive on port 8051
    try:
        # pylint: disable=consider-using-with
        response = urllib.request.urlopen("http://localhost:8051/", timeout=3)
        if response.status == 200:
            return True
    except Exception as e:  # pylint: disable=broad-exception-caught
        print(f"[HEALTHCHECK] Streamlit server is not responding: {e}")
        return False

    print("[HEALTHCHECK] Streamlit returned a non-200 response!")
    return False


if __name__ == "__main__":
    if check_health():
        sys.exit(0)
    sys.exit(1)
