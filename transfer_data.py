# transfer_data.py — load/save entries and append to the audit log

import json
from pathlib import Path
import shutil
from datetime import datetime

DATA_FILE = Path(__file__).resolve().parent / "target.json"
LOG_FILE  = Path(__file__).resolve().parent / "weekly_log.jsonl"


# ---------- entries ----------

def load_entries():
    if not DATA_FILE.exists():
        return []

    text = DATA_FILE.read_text(encoding="utf-8").strip()
    if not text:
        return []

    data = json.loads(text)

    if not isinstance(data, list):
        raise ValueError(
            f"{DATA_FILE} should contain a JSON list, got {type(data).__name__}"
        )

    return data


def save_all(entries):
    if DATA_FILE.exists():
        backup = DATA_FILE.with_suffix(".json.bak")
        shutil.copy2(DATA_FILE, backup)

    DATA_FILE.write_text(
        json.dumps(entries, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )


def save_entry(entry):
    entries = load_entries()
    entries.append(entry)
    save_all(entries)


# ---------- audit log ----------

def append_log(event):
    """Append one JSON object per line. Never rewrites the file."""
    event = {"ts": datetime.now().isoformat(timespec="seconds"), **event}
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")
