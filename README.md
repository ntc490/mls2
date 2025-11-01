Absolutely — here’s a complete **Markdown design document** that summarizes everything we’ve discussed so far:
architecture, behavior, UI design, key interactions, and a few ASCII mockups for both the **CLI / shell-style interface** and the **mobile-friendly web version**.

You could drop this straight into a project README to guide your build.

---

# 📱 Church Messaging Assistant

*A local-first text-based app for managing ministry appointments and assignments*

---

## 🌟 Overview

This app helps streamline communication for church service coordination.
It allows you to:

* Fuzzy search contacts and appointment types
* Compose and send templated text messages
* Use your **own Android phone number** via an on-device SMS gateway
* Track ongoing conversation threads
* Reply inline and close threads when done
* Operate efficiently from either your **laptop** or **phone**, using a **shell-like interface** with **slash commands and pushbuttons**

---

## ⚙️ Architecture

### 🧩 Components

| Component              | Role                                                                                                                        |
| ---------------------- | --------------------------------------------------------------------------------------------------------------------------- |
| **FastAPI backend**    | Runs locally on the Android phone (via Termux). Handles data storage, fuzzy search, and webhook endpoints.                  |
| **SQLite database**    | Stores contacts, appointment templates, and message threads.                                                                |
| **SMS Gateway App**    | Sends/receives messages through the phone’s SIM and HTTP API. Posts incoming messages to FastAPI.                           |
| **Web-based shell UI** | Provides a text-first interface for both phone and laptop use. Styled like a terminal, supports slash commands and buttons. |

---

## 📡 Message Flow

### Sending

1. User types `/new john doe prayer` in the UI.
2. FastAPI uses fuzzy matching to resolve `John Doe` and `Prayer`.
3. The app generates a templated message.
4. Sends message to SMS Gateway API:
   `POST http://127.0.0.1:8080/send-sms`

### Receiving

1. When someone replies, SMS Gateway posts to FastAPI:

   ```json
   { "from": "+15551234567", "message": "Sure, I can do that." }
   ```
2. FastAPI stores the message in `messages` table.
3. UI updates the thread view in real time or on refresh.

### Reliability

* **Option #2 chosen**: Gateway app queues and retries POSTs if the local web server is asleep or unreachable.
* No messages are lost; they arrive once the app wakes up again.

---

## 💾 Data Model (SQLite)

| Table         | Fields                                                      |
| ------------- | ----------------------------------------------------------- |
| **contacts**  | id, first_name, last_name, phone                            |
| **templates** | id, type, text                                              |
| **threads**   | id, contact_id, appointment_type, status (“open”, “closed”) |
| **messages**  | id, thread_id, direction (“in” / “out”), text, timestamp    |

---

## 🔍 Fuzzy Search Logic

* Uses [`rapidfuzz`](https://github.com/maxbachmann/RapidFuzz) for smart matching.
* Context-aware:

  1. No fields filled → search across all (first, last, appointment).
  2. One field filled → narrow scope (e.g., last name for given first).
  3. All matched → ready to create thread.

---

## 🧭 User Interface Design

The UI mimics a **shell interface** with **slash commands** for full control and **pushbuttons** for quick access on mobile.

---

### 🪶 Layout (Split Screen)

```
┌──────────────────────────────┬──────────────────────────────┐
│  🧵 Threads / Inbox          │  ➕ New Thread / Compose      │
│──────────────────────────────┤                              │
│ [*] John D. – Prayer         │ First:  Jo▮                  │
│ [ ] Mary A. – Interview      │ Last:   D▮                   │
│ [ ] Ethan K. – Follow-up     │ Type:   Pra▮                 │
│                              │                              │
│                              │ Message: Hi John, could you  │
│                              │ say a prayer this Sunday?    │
│                              │                              │
│                              │ > /new john doe prayer       │
│                              │ [Send] [Reply] [Close] [Back]│
└──────────────────────────────┴──────────────────────────────┘
```

---

### 🧵 Thread View

```
┌──────────────────────────────┐
│ 🧵 John Doe – Prayer          │
│──────────────────────────────│
│ [You] Hi John, could you say │
│       a prayer this Sunday?  │
│ [John] Sure, happy to!       │
│                              │
│ > /reply “Thanks John!”      │
│                              │
│ [Send] [Close] [Back]        │
└──────────────────────────────┘
```

---

### 🖱️ Mobile UI Mockup (Simplified)

```
───────────────────────────────
 Church Messaging Assistant
───────────────────────────────
[ Threads ] [ Compose ] [ Inbox ]

> /new mary interview
Did you mean:
  1. Mary Adams – Interview
  2. Mary Allen – Prayer
Select: 1

✅ Thread created with Mary Adams
───────────────────────────────
[ New ] [ Reply ] [ Close ] [ Back ]
───────────────────────────────
```

---

## 💬 Slash Commands Reference

| Command                      | Description                  |
| ---------------------------- | ---------------------------- |
| `/new [first] [last] [type]` | Create new thread            |
| `/reply [message]`           | Reply to active thread       |
| `/close [id or current]`     | Close a thread               |
| `/search [term]`             | Search across names or types |
| `/clear`                     | Clear active fields          |
| `/back`                      | Return to thread list        |
| `/help`                      | Show available commands      |

---

## ⌨️ Keyboard Shortcuts (for Laptop Use)

| Key     | Action               |
| ------- | -------------------- |
| `Tab`   | Switch panes         |
| `↑ / ↓` | Navigate thread list |
| `Enter` | Send or select       |
| `c`     | Close thread         |
| `r`     | Reply                |
| `n`     | Start new thread     |
| `/`     | Begin fuzzy search   |
| `q`     | Quit                 |

> On mobile, these are replaced by **slash commands** and **tap buttons**.

---

## 🔋 Device Setup (Summary)

**Environment:**

* Android phone running [Termux](https://termux.dev/en/)
* SMS Gateway API app (or SMSSync)
* FastAPI + SQLite

**Steps:**

1. Install Termux and required packages:

   ```bash
   pkg install python
   pip install fastapi uvicorn rapidfuzz sqlite-utils
   ```
2. Run FastAPI app:

   ```bash
   termux-wake-lock
   uvicorn app:app --host 0.0.0.0 --port 5000
   ```
3. Configure SMS Gateway API app:

   * Outgoing URL: `http://127.0.0.1:8080/send-sms`
   * Incoming webhook: `http://127.0.0.1:5000/incoming`
   * Enable **retry queue** for delivery.
4. Disable battery optimization for both Termux and SMS Gateway app.

---

## 🧱 Future Enhancements

* 🔔 Notifications for new incoming messages
* 📋 CSV import/export for contacts
* 🧠 Smart templates (auto-fill date/time/place)
* ☁️ Optional cloud backup or relay
* 🪶 Theming (dark / light terminal styles)

---

## ✅ Summary

**Your App Will:**

* Run locally on your Android phone (private and offline).
* Use your real phone number for SMS via a gateway app.
* Provide a **text-first “shell” interface** that works on both laptop and phone.
* Use **slash commands + tap buttons** for input.
* Keep your data synced in a local SQLite database.
* Handle message delivery robustly via queued retries.

---

Would you like me to extend this Markdown doc with a **basic project structure and file layout** (FastAPI + HTML shell UI + SMS endpoints + fuzzy search placeholder)?
That would give you a concrete scaffold to start coding from.
