🔥 Awesome — let’s build this into a **runnable prototype**!

The goal:
✅ Fully runnable in **Termux on Android**
✅ Local **FastAPI server**
✅ Minimal **SQLite persistence**
✅ **SMS send/receive** endpoints (simulated or real, depending on your gateway)
✅ A basic **terminal-style web UI** that actually works

You’ll be able to **open your browser to your phone’s IP** (or localhost) and interact with it just like the design.

---

# 🧱 Church Messaging Assistant (Runnable Prototype)

## 📂 Project Structure

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
├── requirements.txt
└── README.md
```

---

## ⚙️ Installation (Termux)

```bash
pkg install python git
pip install fastapi uvicorn jinja2 rapidfuzz requests sqlite-utils
```

Then create the database:

```bash
python -c "import sqlite3; conn=sqlite3.connect('app.db'); \
conn.executescript(open('schema.sql').read()); conn.close()"
```

Or just let the app create tables automatically on first run (it will do this).

---

## 🧠 `app/main.py`

```python
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from . import database, fuzzy, sms

app = FastAPI()
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

# Home: list open threads
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    threads = database.get_open_threads()
    return templates.TemplateResponse("index.html", {"request": request, "threads": threads})

# Slash command handler
@app.post("/command")
async def command(cmd: str = Form(...)):
    response = ""
    if cmd.startswith("/new"):
        _, *terms = cmd.split()
        if not terms:
            response = "Usage: /new [name or appointment]"
        else:
            matches = fuzzy.search_combined(" ".join(terms))
            if matches:
                response = "Found: " + ", ".join(matches[:5])
            else:
                response = "No matches."
    elif cmd.startswith("/reply"):
        response = "Reply feature not implemented yet."
    elif cmd.startswith("/close"):
        response = "Thread closed (simulated)."
    else:
        response = "Unknown command."
    return {"output": response}

# Endpoint for SMS gateway (incoming messages)
@app.post("/incoming")
async def incoming_sms(request: Request):
    data = await request.json()
    sender = data.get("from")
    message = data.get("message")
    database.save_incoming(sender, message)
    return {"status": "ok"}
```

---

## 💾 `app/database.py`

```python
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
```

---

## 💬 `app/sms.py`

```python
import requests

GATEWAY_URL = "http://127.0.0.1:8080/send-sms"

def send_sms(to: str, message: str):
    try:
        res = requests.post(GATEWAY_URL, json={"phone": to, "message": message}, timeout=5)
        return res.status_code
    except Exception as e:
        return str(e)
```

---

## 🔍 `app/fuzzy.py`

```python
from rapidfuzz import process

# Temporary in-memory data for demo
names = ["John Doe", "Mary Adams", "Ethan Kim"]
appointments = ["Prayer", "Interview", "Follow-up"]

def search_combined(term: str):
    data = names + appointments
    matches = process.extract(term, data, limit=5)
    return [m[0] for m in matches if m[1] > 60]
```

---

## 🎨 `app/templates/index.html`

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
          <li>#{{t['id']}} — {{t['appointment_type'] or 'Unknown'}}</li>
        {% endfor %}
      </ul>
    </div>
    <div id="right-pane">
      <div id="terminal-output"></div>
      <form id="cmd-form">
        <input id="cmd" name="cmd" placeholder="/new john prayer" autofocus />
      </form>
    </div>
  </div>
</body>
</html>
```

---

## 💅 `app/static/style.css`

```css
body {
  background: #111;
  color: #eee;
  font-family: monospace;
  display: flex;
  height: 100vh;
  margin: 0;
}
#container { display: flex; flex: 1; }
#left-pane, #right-pane {
  flex: 1;
  padding: 1em;
  border-right: 1px solid #333;
  overflow-y: auto;
}
#cmd {
  width: 100%;
  background: #222;
  color: #0f0;
  border: none;
  padding: 0.5em;
}
#terminal-output div {
  margin: 0.25em 0;
}
```

---

## ⚙️ `app/static/script.js`

```javascript
document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("cmd-form");
  const input = document.getElementById("cmd");
  const output = document.getElementById("terminal-output");

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const cmd = input.value.trim();
    if (!cmd) return;

    output.innerHTML += `<div>> ${cmd}</div>`;
    const formData = new FormData();
    formData.append("cmd", cmd);

    const res = await fetch("/command", { method: "POST", body: formData });
    const data = await res.json();
    output.innerHTML += `<div>${data.output}</div>`;
    output.scrollTop = output.scrollHeight;
    input.value = "";
  });
});
```

---

## ✅ Run It

In Termux:

```bash
termux-wake-lock
uvicorn app.main:app --host 0.0.0.0 --port 5000
```

Then open your browser on your phone or laptop:

```
http://<your-phone-ip>:5000
```

You’ll see your **split-screen “terminal” interface** — try commands like:

```
/new john prayer
/new interview
```

You’ll get fuzzy matches and simulated output!

---

## 🧩 Next Steps (Future Iterations)

* [ ] Implement real fuzzy contact lookup from SQLite
* [ ] Add `/reply` and `/close` logic
* [ ] Hook `/send` to your actual SMS gateway
* [ ] Add message thread view and reply window
* [ ] Add CSV import for contact list

---

Would you like me to extend this prototype next to **support real fuzzy searching over a CSV of contacts** (so you can import your actual contact list and use it live)?
That would make it fully personalized and practical.
