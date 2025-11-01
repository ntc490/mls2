import sqlite3
from pathlib import Path

DB_PATH = Path("app.db")

def connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init():
    with connect() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS contacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT,
            last_name TEXT,
            phone TEXT
        );
        CREATE TABLE IF NOT EXISTS threads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            contact_id INTEGER,
            appointment_type TEXT,
            status TEXT DEFAULT 'open'
        );
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            thread_id INTEGER,
            direction TEXT,
            text TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        """)
        conn.commit()

def get_open_threads():
    init()
    with connect() as conn:
        c = conn.execute("SELECT id, contact_id, appointment_type FROM threads WHERE status='open'")
        return c.fetchall()

def save_incoming(phone, text):
    init()
    with connect() as conn:
        conn.execute(
            "INSERT INTO messages (thread_id, direction, text) VALUES (NULL, 'in', ?)",
            (text,)
        )
        conn.commit()
