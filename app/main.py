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
