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
