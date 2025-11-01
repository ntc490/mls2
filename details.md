Excellent 🙌 — this is where your app starts becoming *personally useful*!

Let’s extend the **Church Messaging Assistant** prototype to support:
✅ Importing contacts from a CSV file
✅ Fuzzy searching *real* names (first + last)
✅ Creating new threads that connect to a contact record

---

# 🧱 Church Messaging Assistant — CSV Contact + Fuzzy Search Upgrade

---

## 🧩 What’s New

1. **CSV contact import** (via `/import` command or startup)
2. **Fuzzy search** now matches across:

   * First names
   * Last names
   * Full names (for flexibility)
3. **Thread creation** associates the fuzzy match with a real contact
4. Database auto-creates threads when `/new` is issued with a name + appointment type

---

## 📂 Updated Project Structure

```
church-messaging-assistant/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── database.py
│   ├── sms.py
│   ├── fuzzy.py
│   ├── static/
│   │   ├── style.css
│   │   └── script.js
│   └── templates/
│       └── index.html
├── contacts.csv
├── requirements.txt
└── README.md
```

---

## 📄 Example `contacts.csv`

```csv
first_name,last_name,phone
John,Doe,+15551234567
Mary,Adams,+15559876543
Ethan,Kim,+15552345678
```

---

## 💾 Updated `app/database.py`

Now includes CSV import and contact lookup helpers.

```python
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
```

---

## 🔍 Updated `app/fuzzy.py`

Now searches against your actual contacts.

```python
from rapidfuzz import process
from . import database

def fuzzy_search_name(term):
    contacts = database.get_contacts()
    names = [f"{c['first_name']} {c['last_name']}" for c in contacts]
    matches = process.extract(term, names, limit=5)
    return [m[0] for m in matches if m[1] > 60]

def resolve_contact(name):
    """Return phone number for a matched name."""
    contacts = database.get_contacts()
    for c in contacts:
        full = f"{c['first_name']} {c['last_name']}"
        if full.lower() == name.lower():
            return c["phone"]
    return None

def search_combined(term):
    # For future expansion (names + appointment types)
    return fuzzy_search_name(term)
```

---

## 🚀 Updated `app/main.py`

Now handles `/new` commands with real contact resolution.

```python
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from . import database, fuzzy, sms

app = FastAPI()
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

@app.on_event("startup")
def startup():
    database.init()
    database.import_contacts()

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    threads = database.get_open_threads()
    return templates.TemplateResponse("index.html", {"request": request, "threads": threads})

@app.post("/command")
async def command(cmd: str = Form(...)):
    cmd = cmd.strip()
    output = ""
    if cmd.startswith("/new"):
        _, *args = cmd.split()
        if not args:
            output = "Usage: /new [name or part of name] [appointment type]"
        else:
            text = " ".join(args)
            matches = fuzzy.fuzzy_search_name(text)
            if not matches:
                output = f"No matches for '{text}'."
            else:
                name = matches[0]
                phone = fuzzy.resolve_contact(name)
                if phone:
                    database.create_thread(phone, "Appointment")
                    output = f"✅ Created new thread with {name} ({phone})"
                else:
                    output = f"Could not resolve contact for {name}."
    elif cmd == "/import":
        database.import_contacts()
        output = "Contacts imported."
    else:
        output = f"Unknown command: {cmd}"
    return {"output": output}

@app.post("/incoming")
async def incoming_sms(request: Request):
    data = await request.json()
    sender = data.get("from")
    message = data.get("message")
    database.save_incoming(sender, message)
    return {"status": "ok"}
```

---

## ✅ Try It Out

1. Place your `contacts.csv` file beside your app.
2. Start your FastAPI app:

   ```bash
   termux-wake-lock
   uvicorn app.main:app --host 0.0.0.0 --port 5000
   ```
3. Visit from browser:

   ```
   http://<your-phone-ip>:5000
   ```
4. Try:

   ```
   /new mary prayer
   /new john interview
   /import
   ```

You’ll see real fuzzy matches based on your CSV file, and new threads will appear in the left pane.

---

## 🧠 Future Improvements

| Feature     | Description                                 |
| ----------- | ------------------------------------------- |
| `/reply`    | Allow inline reply messages via SMS gateway |
| `/close`    | Archive a thread                            |
| `/threads`  | List open and closed threads                |
| `/search`   | Search for any name                         |
| `/template` | Select or create message templates          |

---

Would you like me to take this one more step — make `/reply` actually send a message through your SMS gateway (and record it in the DB)?
That would make it a **fully functioning two-way text system**, ready to use in real life.
