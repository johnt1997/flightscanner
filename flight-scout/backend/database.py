"""
Flight Scout Database - SQLite backend for users, saved deals, and price alerts.
"""

import sqlite3
import hashlib
import hmac
import base64
import time
import os

# Use /data volume on Railway (persists across deploys), fallback to local for dev
_data_dir = "/data" if os.path.isdir("/data") else os.path.dirname(__file__)
DB_PATH = os.path.join(_data_dir, "flight_scout.db")
TOKEN_SECRET = os.environ.get("FLIGHT_SCOUT_SECRET", "flight-scout-default-secret-key")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS saved_deals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            city TEXT NOT NULL,
            country TEXT NOT NULL,
            price REAL NOT NULL,
            departure_date TEXT,
            return_date TEXT,
            flight_time TEXT,
            is_direct INTEGER DEFAULT 0,
            url TEXT,
            origin TEXT,
            latitude REAL DEFAULT 0,
            longitude REAL DEFAULT 0,
            saved_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS price_alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            destination_city TEXT NOT NULL,
            max_price REAL NOT NULL,
            telegram_chat_id TEXT NOT NULL,
            active INTEGER DEFAULT 1,
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS deal_alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            airport TEXT NOT NULL DEFAULT 'vie',
            max_price REAL NOT NULL DEFAULT 50,
            telegram_chat_id TEXT NOT NULL,
            active INTEGER DEFAULT 1,
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS search_cache (
            key TEXT PRIMARY KEY,
            data TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS saved_searches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            params TEXT NOT NULL,
            results TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS search_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            search_mode TEXT NOT NULL,
            airports TEXT NOT NULL,
            start_date TEXT,
            end_date TEXT,
            max_price REAL,
            results_count INTEGER DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
    """)
    conn.close()


# --- Auth ---

def hash_password(password: str) -> str:
    import bcrypt
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, password_hash: str) -> bool:
    import bcrypt
    return bcrypt.checkpw(password.encode(), password_hash.encode())


def create_token(user_id: int) -> str:
    timestamp = str(int(time.time()))
    payload = f"{user_id}:{timestamp}"
    signature = hmac.new(TOKEN_SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()[:16]
    token_data = f"{payload}:{signature}"
    return base64.b64encode(token_data.encode()).decode()


def verify_token(token: str) -> int | None:
    try:
        token_data = base64.b64decode(token.encode()).decode()
        parts = token_data.split(":")
        if len(parts) != 3:
            return None
        user_id, timestamp, signature = parts
        expected = hmac.new(TOKEN_SECRET.encode(), f"{user_id}:{timestamp}".encode(), hashlib.sha256).hexdigest()[:16]
        if not hmac.compare_digest(signature, expected):
            return None
        uid = int(user_id)
        conn = get_db()
        row = conn.execute("SELECT id FROM users WHERE id = ?", (uid,)).fetchone()
        conn.close()
        if not row:
            return None
        return uid
    except Exception:
        return None


# --- Users ---

def create_user(username: str, password: str) -> dict | None:
    conn = get_db()
    try:
        pw_hash = hash_password(password)
        cursor = conn.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            (username, pw_hash)
        )
        conn.commit()
        return {"id": cursor.lastrowid, "username": username}
    except sqlite3.IntegrityError:
        return None
    finally:
        conn.close()


def authenticate_user(username: str, password: str) -> dict | None:
    conn = get_db()
    row = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    conn.close()
    if row and verify_password(password, row["password_hash"]):
        return {"id": row["id"], "username": row["username"]}
    return None


# --- Saved Deals ---

def save_deal(user_id: int, deal: dict) -> int:
    conn = get_db()
    existing = conn.execute(
        "SELECT id FROM saved_deals WHERE user_id = ? AND city = ? AND departure_date = ? AND return_date = ?",
        (user_id, deal["city"], deal.get("departure_date"), deal.get("return_date"))
    ).fetchone()
    if existing:
        conn.close()
        return existing["id"]
    cursor = conn.execute(
        """INSERT INTO saved_deals
           (user_id, city, country, price, departure_date, return_date, flight_time, is_direct, url, origin, latitude, longitude)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (user_id, deal["city"], deal["country"], deal["price"],
         deal.get("departure_date"), deal.get("return_date"), deal.get("flight_time"),
         1 if deal.get("is_direct") else 0, deal.get("url"), deal.get("origin"),
         deal.get("latitude", 0), deal.get("longitude", 0))
    )
    conn.commit()
    deal_id = cursor.lastrowid
    conn.close()
    return deal_id


def get_user_deals(user_id: int) -> list[dict]:
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM saved_deals WHERE user_id = ? ORDER BY saved_at DESC", (user_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def delete_deal(user_id: int, deal_id: int) -> bool:
    conn = get_db()
    cursor = conn.execute(
        "DELETE FROM saved_deals WHERE id = ? AND user_id = ?", (deal_id, user_id)
    )
    conn.commit()
    deleted = cursor.rowcount > 0
    conn.close()
    return deleted


# --- Price Alerts ---

def create_alert(user_id: int, destination_city: str, max_price: float, telegram_chat_id: str) -> int:
    conn = get_db()
    cursor = conn.execute(
        """INSERT INTO price_alerts (user_id, destination_city, max_price, telegram_chat_id)
           VALUES (?, ?, ?, ?)""",
        (user_id, destination_city, max_price, telegram_chat_id)
    )
    conn.commit()
    alert_id = cursor.lastrowid
    conn.close()
    return alert_id


def get_user_alerts(user_id: int) -> list[dict]:
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM price_alerts WHERE user_id = ? AND active = 1 ORDER BY created_at DESC",
        (user_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_all_active_alerts() -> list[dict]:
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM price_alerts WHERE active = 1"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def delete_alert(user_id: int, alert_id: int) -> bool:
    conn = get_db()
    cursor = conn.execute(
        "DELETE FROM price_alerts WHERE id = ? AND user_id = ?", (alert_id, user_id)
    )
    conn.commit()
    deleted = cursor.rowcount > 0
    conn.close()
    return deleted


# --- Deal Alerts ---

def create_deal_alert(user_id: int, airport: str, max_price: float, telegram_chat_id: str) -> int:
    conn = get_db()
    # Max 2 alerts per user
    count = conn.execute("SELECT COUNT(*) as c FROM deal_alerts WHERE user_id = ? AND active = 1", (user_id,)).fetchone()["c"]
    if count >= 2:
        conn.close()
        return -1
    cursor = conn.execute(
        "INSERT INTO deal_alerts (user_id, airport, max_price, telegram_chat_id) VALUES (?, ?, ?, ?)",
        (user_id, airport, max_price, telegram_chat_id)
    )
    conn.commit()
    alert_id = cursor.lastrowid
    conn.close()
    return alert_id


def get_user_deal_alerts(user_id: int) -> list[dict]:
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM deal_alerts WHERE user_id = ? AND active = 1 ORDER BY created_at DESC",
        (user_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_all_active_deal_alerts() -> list[dict]:
    conn = get_db()
    rows = conn.execute("SELECT * FROM deal_alerts WHERE active = 1").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def delete_deal_alert(user_id: int, alert_id: int) -> bool:
    conn = get_db()
    cursor = conn.execute("DELETE FROM deal_alerts WHERE id = ? AND user_id = ?", (alert_id, user_id))
    conn.commit()
    deleted = cursor.rowcount > 0
    conn.close()
    return deleted


# --- Search Cache ---

CACHE_TTL_HOURS = 3

def get_cache(key: str) -> dict | None:
    import json
    conn = get_db()
    row = conn.execute(
        "SELECT data, created_at FROM search_cache WHERE key = ?", (key,)
    ).fetchone()
    conn.close()
    if not row:
        return None
    from datetime import datetime, timedelta
    created = datetime.fromisoformat(row["created_at"])
    if datetime.utcnow() - created > timedelta(hours=CACHE_TTL_HOURS):
        return None
    return json.loads(row["data"])


def set_cache(key: str, data: dict):
    import json
    conn = get_db()
    conn.execute(
        "INSERT OR REPLACE INTO search_cache (key, data, created_at) VALUES (?, ?, datetime('now'))",
        (key, json.dumps(data))
    )
    # Cleanup expired entries
    conn.execute(
        f"DELETE FROM search_cache WHERE created_at < datetime('now', '-{CACHE_TTL_HOURS} hours')"
    )
    conn.commit()
    conn.close()


# --- Search Log ---

def log_search(user_id: int, search_mode: str, airports: str, start_date: str, end_date: str, max_price: float, results_count: int = 0):
    conn = get_db()
    conn.execute(
        """INSERT INTO search_log (user_id, search_mode, airports, start_date, end_date, max_price, results_count)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (user_id, search_mode, airports, start_date, end_date, max_price, results_count)
    )
    conn.commit()
    conn.close()


def update_search_results(search_id: int, results_count: int):
    conn = get_db()
    conn.execute("UPDATE search_log SET results_count = ? WHERE id = ?", (results_count, search_id))
    conn.commit()
    conn.close()


def get_all_users() -> list[dict]:
    conn = get_db()
    rows = conn.execute("""
        SELECT u.id, u.username, u.created_at,
               COUNT(DISTINCT s.id) as search_count,
               MAX(s.created_at) as last_search
        FROM users u
        LEFT JOIN search_log s ON u.id = s.user_id
        GROUP BY u.id
        ORDER BY u.created_at DESC
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_search_log(limit: int = 50) -> list[dict]:
    conn = get_db()
    rows = conn.execute("""
        SELECT s.*, u.username
        FROM search_log s
        JOIN users u ON s.user_id = u.id
        ORDER BY s.created_at DESC
        LIMIT ?
    """, (limit,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# --- Saved Searches ---

def save_search(user_id: int, name: str, params: str, results: str) -> int:
    import json
    conn = get_db()
    count = conn.execute("SELECT COUNT(*) FROM saved_searches WHERE user_id = ?", (user_id,)).fetchone()[0]
    if count >= 5:
        conn.close()
        return -1
    cursor = conn.execute(
        "INSERT INTO saved_searches (user_id, name, params, results) VALUES (?, ?, ?, ?)",
        (user_id, name, params, results)
    )
    conn.commit()
    search_id = cursor.lastrowid
    conn.close()
    return search_id


def get_user_searches(user_id: int) -> list[dict]:
    import json
    conn = get_db()
    rows = conn.execute(
        "SELECT id, name, params, results, created_at, updated_at FROM saved_searches WHERE user_id = ? ORDER BY updated_at DESC",
        (user_id,)
    ).fetchall()
    conn.close()
    result = []
    for r in rows:
        d = dict(r)
        p = json.loads(d["params"])
        d["airports"] = p.get("airports", [])
        d["search_mode"] = p.get("search_mode", "everywhere")
        d["start_date"] = p.get("start_date", "")
        d["end_date"] = p.get("end_date", "")
        d["result_count"] = len(json.loads(d["results"])) if d.get("results") else 0
        del d["params"]
        del d["results"]
        result.append(d)
    return result


def get_saved_search(user_id: int, search_id: int) -> dict | None:
    conn = get_db()
    row = conn.execute(
        "SELECT * FROM saved_searches WHERE id = ? AND user_id = ?", (search_id, user_id)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def update_search_results(user_id: int, search_id: int, results: str) -> bool:
    conn = get_db()
    cursor = conn.execute(
        "UPDATE saved_searches SET results = ?, updated_at = datetime('now') WHERE id = ? AND user_id = ?",
        (results, search_id, user_id)
    )
    conn.commit()
    updated = cursor.rowcount > 0
    conn.close()
    return updated


def delete_saved_search(user_id: int, search_id: int) -> bool:
    conn = get_db()
    cursor = conn.execute("DELETE FROM saved_searches WHERE id = ? AND user_id = ?", (search_id, user_id))
    conn.commit()
    deleted = cursor.rowcount > 0
    conn.close()
    return deleted


# Init DB on import
init_db()
