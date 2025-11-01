Perfect 👍 — below is the **extended Markdown design document**, now including a **starter project structure**, **file layout**, and **example code scaffolding** for your app.

This gives you a concrete foundation to start building your **Church Messaging Assistant** in FastAPI + HTML (terminal-style UI) on your Android phone.

---

# 📱 Church Messaging Assistant

*A local-first text-based app for managing ministry appointments and assignments*

---

## 🌟 Overview

This app helps streamline communication for church coordination.
It runs locally on your **Android phone** (via Termux) and uses an **SMS gateway app** to send and receive texts through your real phone number.

### Core Capabilities

* Fuzzy search on names and appointment types
* Message templating for quick communication
* Two-way SMS handling (send + receive)
* Thread tracking and completion status
* Shell-like web UI with slash commands and shortcut buttons
* Works from both your **phone** and **laptop** (on same Wi-Fi)

---

## 🧩 Architecture Summary

| Component                       | Role                                                          |
| ------------------------------- | ------------------------------------------------------------- |
| **FastAPI app**                 | Core backend; manages data, templates, SMS send/receive       |
| **SQLite DB**                   | Persistent local storage                                      |
| **SMS Gateway App**             | Sends/receives messages via the phone’s SIM; exposes HTTP API |
| **HTML/JS “terminal” frontend** | Provides shell-like command interface                         |
| **Termux environment**          | Runs everything locally on Android                            |

---

## 📁 Project Structure

```
church-messaging-assistant/
├── app/
│   ├── __init__.py
│   ├── main.py                # FastAPI entrypoint
│   ├── database.py            # SQLite connection helpers
│   ├── models.py              # DB schema definitions
│   ├── sms.py                 # Functions for sending messages via gateway
│   ├── fuzzy.py               # Fuzzy matching logic
│   ├── templates.py           # Message template handling
│   └── static/
│       ├── style.css          # Terminal-style CSS
│       └── script.js          # Slash command + button logic
│
├── templates/
│   └── index.html             # Web terminal UI
│
├── requirements.txt
└── README.md
```

---

## 🧠 Database Schema

```sql
-- contacts
CREATE TABLE contacts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name TEXT,
    last_name TEXT,
    phone TEXT
);

-- templates
CREATE TABLE templates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    type TEXT,
    text TEXT
);

-- threads
CREATE TABLE threads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contact_id INTEGER,
    appointment_type TEXT,
    status TEXT DEFAULT 'open'
);

-- messages
CREATE TABLE messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    thread_id INTEGER,
    direction TEXT CHECK(direction IN ('in', 'out')),
    text TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

---

## 🧰 FastAPI App Scaffold

### `app/main.py`

```python
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from . import sms, database, fuzzy

app = FastAPI()
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    threads = database.get_open_threads()
    return templates.TemplateResponse("index.html", {"request": request, "threads": threads})

@app.post("/send")
async def send_sms(to: str = Form(...), message: str = Form(...)):
    result = sms.send_sms(to, message)
    database.save_message(to, message, direction="out")
    return {"status": "sent", "result": result}

@app.post("/incoming")
async def incoming_sms(request: Request):
    data = await request.json()
    sender = data.get("from")
    message = data.get("message")
    database.save_message(sender, message, direction="in")
    return {"status": "ok"}
```

---

### `app/sms.py`

```python
import requests

GATEWAY_URL = "http://127.0.0.1:8080/send-sms"

def send_sms(to: str, message: str):
    payload = {"phone": to, "message": message}
    try:
        res = requests.post(GATEWAY_URL, json=payload, timeout=5)
        return res.status_code
    except Exception as e:
        return str(e)
```

---

### `app/fuzzy.py`

```python
from rapidfuzz import process

def fuzzy_search(term, dataset):
    matches = process.extract(term, dataset, limit=5)
    return [m[0] for m in matches if m[1] > 60]
```

---

### `app/database.py`

```python
import sqlite3

DB_PATH = "app.db"

def connect():
    return sqlite3.connect(DB_PATH)

def get_open_threads():
    with connect() as conn:
        c = conn.cursor()
        c.execute("SELECT id, contact_id, appointment_type FROM threads WHERE status='open'")
        return c.fetchall()

def save_message(phone, text, direction):
    with connect() as conn:
        c = conn.cursor()
        c.execute(
            "INSERT INTO messages (thread_id, direction, text) VALUES ((SELECT id FROM contacts WHERE phone=? LIMIT 1), ?, ?)",
            (phone, direction, text)
        )
        conn.commit()
```

---

## 🎨 Web UI: Terminal-Style Interface

### `templates/index.html`

```html
<!DOCTYPE html>
<html>
<head>
  <link rel="stylesheet" href="/static/style.css">
  <script src="/static/script.js" defer></script>
</head>
<body>
  <div id="container">
    <div id="left-pane">
      <h3>🧵 Threads</h3>
      <ul id="threads">
        {% for t in threads %}
          <li>[{{ t[0] }}] Contact {{ t[1] }} – {{ t[2] }}</li>
        {% endfor %}
      </ul>
    </div>
    <div id="right-pane">
      <h3>💬 Command</h3>
      <div id="terminal-output"></div>
      <form id="command-form">
        <input type="text" id="command-input" placeholder="/new john doe prayer" autofocus>
      </form>
      <div id="buttons">
        <button data-cmd="/new">New</button>
        <button data-cmd="/reply">Reply</button>
        <button data-cmd="/close">Close</button>
        <button data-cmd="/back">Back</button>
      </div>
    </div>
  </div>
</body>
</html>
```

---

### `app/static/style.css`

```css
body {
  background: #111;
  color: #eee;
  font-family: monospace;
  display: flex;
  height: 100vh;
  margin: 0;
}
#container {
  display: flex;
  flex: 1;
}
#left-pane, #right-pane {
  flex: 1;
  padding: 1em;
  border-right: 1px solid #333;
  overflow-y: auto;
}
#command-input {
  width: 100%;
  background: #222;
  color: #0f0;
  border: none;
  padding: 0.5em;
}
#buttons button {
  background: #333;
  color: #fff;
  margin: 0.25em;
  border: 1px solid #555;
  padding: 0.5em 1em;
}
```

---

### `app/static/script.js`

```javascript
document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("command-form");
  const input = document.getElementById("command-input");
  const output = document.getElementById("terminal-output");
  const buttons = document.querySelectorAll("#buttons button");

  buttons.forEach(btn => {
    btn.addEventListener("click", () => {
      input.value = btn.dataset.cmd + " ";
      input.focus();
    });
  });

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const cmd = input.value.trim();
    output.innerHTML += `<div>> ${cmd}</div>`;
    input.value = "";

    if (cmd.startsWith("/new")) {
      output.innerHTML += `<div>Creating new thread...</div>`;
      // TODO: handle fuzzy search + backend call
    }
    if (cmd.startsWith("/reply")) {
      output.innerHTML += `<div>Replying...</div>`;
    }
  });
});
```

---

## 🧱 Example Slash Command Flow

```
> /new john prayer
→ Found matches:
   1. John Doe – Prayer
   2. John Dalton – Prayer
Select: 1
✅ Thread created with John Doe.

> /reply Sure, thank you!
✅ Sent to +15555551234
```

---

## ⚙️ Local Setup in Termux

```bash
pkg install python git
pip install fastapi uvicorn jinja2 rapidfuzz requests

# Run server
termux-wake-lock
uvicorn app.main:app --host 0.0.0.0 --port 5000
```

Then open in your phone browser or laptop:
👉 `http://<your-phone-ip>:5000`

---

## ✅ Summary

* Local-first app (no cloud dependency)
* Real SMS via your own number
* Smart fuzzy search and slash commands
* Works from both phone and laptop
* Message delivery reliable via SMS gateway queue
* Minimal setup in Termux

---

Would you like me to extend this further into a **runnable prototype** (i.e., minimal working code with fuzzy search, send + receive demo, and thread persistence)?
I can make sure it’s small enough to test directly in Termux.
