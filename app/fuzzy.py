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
