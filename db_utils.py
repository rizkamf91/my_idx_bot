# db_utils.py

import json
from datetime import date

DB_FILE = "user_db.json"
LIMIT_FREE = 20

def load_db():
    try:
        with open(DB_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_db(db):
    with open(DB_FILE, "w") as f:
        json.dump(db, f, indent=2)

def check_daily_limit(user_id: int, status: str) -> bool:
    """
    Batasi user free hanya 20 request/hari.
    Premium tanpa limit.
    """
    db = load_db()
    user = db.get(str(user_id)) or {"requests": 0, "last_date": str(date.today()), "status": status}
    # Reset counter tiap hari
    if user["last_date"] != str(date.today()):
        user["requests"] = 0
        user["last_date"] = str(date.today())

    if status == "free" and user["requests"] >= LIMIT_FREE:
        return False

    user["requests"] += 1
    db[str(user_id)] = user
    save_db(db)
    return True
