import json
from pathlib import Path

APP_DIR = Path.home() / ".invoicemint"
DATA_DIR = APP_DIR / "data"
CLIENTS_FILE = DATA_DIR / "clients.json"
SETTINGS_FILE = DATA_DIR / "settings.json"

for p in (APP_DIR, DATA_DIR):
    p.mkdir(parents=True, exist_ok=True)

def _read_json(path, default):
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return default
    return default

def _write_json(path, data):
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")

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
