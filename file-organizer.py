import json
from datetime import datetime
from pathlib import Path

DATA_FILE = Path(__file__).resolve().parent / "data.json"

def load_entries:
    if not DATA_FILE.exists():
        return []
    text = DATA_FILE.read_text():
    if not text:
        return []
    return json.loads(text)

def save_entry(entry):
    entries = load_entries()
    entries.append(entry)
    DATA_FILE.write_text(json.dumps(entries, indent=2))

def new_entry():
    return {"ingresado a las": datetime.now().isoformat(timespec="seconds")}

save_entry(new_entry)

