import sqlite3, csv
from pathlib import Path

DB_PATH = Path("app.db")
CONTACTS_CSV = Path("contacts.csv")

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
            phone TEXT UNIQUE
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

def import_contacts():
    """Load contacts from CSV if table is empty."""
    init()
    with connect() as conn:
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM contacts")
        if c.fetchone()[0] > 0:
            return  # already populated

        if not CONTACTS_CSV.exists():
            print("⚠️ No contacts.csv found.")
            return

        with open(CONTACTS_CSV) as f:
            reader = csv.DictReader(f)
            for row in reader:
                c.execute(
                    "INSERT OR IGNORE INTO contacts (first_name, last_name, phone) VALUES (?, ?, ?)",
                    (row["first_name"], row["last_name"], row["phone"]),
                )
        conn.commit()
        print("✅ Contacts imported.")

def get_contacts():
    init()
    import_contacts()
    with connect() as conn:
        c = conn.execute("SELECT first_name, last_name, phone FROM contacts")
        return [dict(row) for row in c.fetchall()]

def get_open_threads():
    init()
    with connect() as conn:
        c = conn.execute("""
            SELECT t.id, c.first_name || ' ' || c.last_name AS name, t.appointment_type
            FROM threads t JOIN contacts c ON t.contact_id = c.id
            WHERE t.status='open'
        """)
        return c.fetchall()

def create_thread(contact_phone, appointment_type):
    """Creates a new thread for a contact and appointment."""
    init()
    with connect() as conn:
        c = conn.cursor()
        c.execute("SELECT id FROM contacts WHERE phone=?", (contact_phone,))
        row = c.fetchone()
        if not row:
            return None
        contact_id = row["id"]
        c.execute(
            "INSERT INTO threads (contact_id, appointment_type) VALUES (?, ?)",
            (contact_id, appointment_type),
        )
        conn.commit()
        return c.lastrowid

def save_incoming(phone, text):
    init()
    with connect() as conn:
        c = conn.cursor()
        c.execute(
            """
            INSERT INTO messages (thread_id, direction, text)
            VALUES (
                (SELECT id FROM threads t
                 JOIN contacts c ON c.id = t.contact_id
                 WHERE c.phone=? AND t.status='open' LIMIT 1),
                'in', ?
            )
            """,
            (phone, text),
        )
        conn.commit()
