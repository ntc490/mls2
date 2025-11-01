from rapidfuzz import process

# Temporary in-memory data for demo
names = ["John Doe", "Mary Adams", "Ethan Kim"]
appointments = ["Prayer", "Interview", "Follow-up"]

def search_combined(term: str):
    data = names + appointments
    matches = process.extract(term, data, limit=5)
    return [m[0] for m in matches if m[1] > 60]
