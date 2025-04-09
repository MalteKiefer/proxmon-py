import os
from datetime import datetime
CONFIG_PATH = os.path.expanduser("~/.config/proxmon/config.json")

def ensure_config_dir():
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)

def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")
    
def format_uptime(seconds):
    if seconds == 0:
        return "-"
    else:
        days = seconds // 86400
        hours = (seconds % 86400) // 3600
        minutes = (seconds % 3600) // 60

        if days > 0:
            return f"{days}d {hours}h {minutes}m"
        else:
            return f"{hours}h {minutes}m"
        
def format_unix_timestamp(ts) -> str:
    try:
        return datetime.fromtimestamp(float(ts)).strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return "-"