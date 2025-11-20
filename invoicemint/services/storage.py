# invoicemint/services/storage.py
import json
from pathlib import Path
from datetime import datetime

APP_DIR = Path.home() / ".invoicemint"
DATA_DIR = APP_DIR / "data"
DRAFTS_DIR = APP_DIR / "drafts"
CLIENTS_FILE = DATA_DIR / "clients.json"
SETTINGS_FILE = DATA_DIR / "settings.json"

for p in (APP_DIR, DATA_DIR, DRAFTS_DIR):
    p.mkdir(parents=True, exist_ok=True)

def _read_json(path, default):
    if Path(path).exists():
        try:
            return json.loads(Path(path).read_text(encoding="utf-8"))
        except Exception:
            return default
    return default

def _write_json(path, data):
    Path(path).write_text(json.dumps(data, indent=2), encoding="utf-8")

DEFAULT_SETTINGS = {"theme": "light", "company": {}}

def load_settings():
    return _read_json(SETTINGS_FILE, DEFAULT_SETTINGS)

def save_settings(data):
    if data is None:
        data = DEFAULT_SETTINGS
    _write_json(SETTINGS_FILE, data)

def load_clients():
    return _read_json(CLIENTS_FILE, [])

def save_clients(clients):
    _write_json(CLIENTS_FILE, clients or [])

# ---------------- Drafts API ---------------- #

def list_drafts():
    """Return a list of available drafts with metadata."""
    items = []
    for p in sorted(DRAFTS_DIR.glob("*.json")):
        try:
            stat = p.stat()
            items.append({
                "name": p.name,
                "path": str(p),
                "mtime": stat.st_mtime,
            })
        except Exception:
            continue
    return items

def save_draft(data: dict, name: str | None = None) -> Path:
    """Save a draft dict to the drafts directory and return its path."""
    if name:
        filename = name if name.endswith(".json") else f"{name}.json"
    else:
        ts = datetime.now().strftime("%Y%m%d-%H%M%S")
        filename = f"invoice-{ts}.json"
    path = DRAFTS_DIR / filename
    _write_json(path, data)
    return path

def load_draft(path: str | Path) -> dict:
    """Load a draft JSON by path (string or Path)."""
    return _read_json(Path(path), {})
