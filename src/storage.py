"""Persistent storage for tracking sent problems."""

import json
import os
from datetime import datetime

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
SENT_FILE = os.path.join(DATA_DIR, "sent.json")


def _ensure_data_dir():
    os.makedirs(DATA_DIR, exist_ok=True)


def load_sent_ids() -> set[str]:
    """Load the set of already-sent problem IDs."""
    _ensure_data_dir()
    if not os.path.exists(SENT_FILE):
        return set()
    with open(SENT_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    return {item["id"] for item in data}


def load_sent_records() -> list[dict]:
    """Load full sent records."""
    _ensure_data_dir()
    if not os.path.exists(SENT_FILE):
        return []
    with open(SENT_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def mark_as_sent(problems: list[dict]):
    """Append problems to the sent records."""
    _ensure_data_dir()
    records = load_sent_records()
    for p in problems:
        records.append({
            "id": f"{p['contestId']}-{p['index']}",
            "name": p.get("name", ""),
            "rating": p.get("rating"),
            "sent_at": datetime.now().isoformat(),
        })
    with open(SENT_FILE, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)
