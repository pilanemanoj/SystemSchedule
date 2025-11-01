import os
import datetime

# By default, use the folder containing the main script
LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "debug.txt")

def log_message(msg):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    full_line = f"[{timestamp}] {msg}\n"
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(full_line)
    except Exception:
        pass

def set_log_file(path):
    global LOG_FILE
    LOG_FILE = path
