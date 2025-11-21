# invoicemint/services/storage.py
import json
import re
from pathlib import Path
from datetime import datetime

# ---------- App directories ----------
APP_DIR = Path.home() / ".invoicemint"
DATA_DIR = APP_DIR / "data"
DRAFTS_DIR = APP_DIR / "drafts"
CLIENTS_FILE = DATA_DIR / "clients.json"
SETTINGS_FILE = DATA_DIR / "settings.json"

for p in (APP_DIR, DATA_DIR, DRAFTS_DIR):
    p.mkdir(parents=True, exist_ok=True)

# ---------- JSON helpers ----------
def _read_json(path, default):
    if Path(path).exists():
        try:
            return json.loads(Path(path).read_text(encoding="utf-8"))
        except Exception:
            return default
    return default

def _write_json(path, data):
    Path(path).write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

# ---------- Settings & Clients ----------
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

# ---------- Drafts API ----------
def list_drafts():
    """Return a list of available drafts with metadata."""
    items = []
    for p in sorted(DRAFTS_DIR.glob("*.json")):
        try:
            stat = p.stat()
            items.append({
                "name": p.stem,
                "path": str(p),
                "mtime": stat.st_mtime,
            })
        except Exception:
            continue
    return items

# --- helpers for named saving ---
_slug_re = re.compile(r"[^A-Za-z0-9._-]+")

def slugify(name: str) -> str:
    name = (name or "").strip()
    if not name:
        return "draft"
    name = name.replace(" ", "-")
    name = _slug_re.sub("", name)
    return name[:80]

def next_available_filename(base_path: Path) -> Path:
    """If base_path exists, append -2, -3, ... until free."""
    if not base_path.exists():
        return base_path
    stem, suffix, parent = base_path.stem, base_path.suffix, base_path.parent
    i = 2
    while True:
        candidate = parent / f"{stem}-{i}{suffix}"
        if not candidate.exists():
            return candidate
        i += 1

def save_json_named(data: dict, name: str) -> Path:
    """Save to drafts/<slug>.json (ensure unique)."""
    slug = slugify(name)
    path = DRAFTS_DIR / f"{slug}.json"
    path = next_available_filename(path)
    _write_json(path, data)
    return path

def save_draft(data: dict, name: str | None = None) -> Path:
    """Save a draft dict to the drafts directory and return its path."""
    if name:
        return save_json_named(data, name)
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    filename = f"invoice-{ts}.json"
    path = DRAFTS_DIR / filename
    _write_json(path, data)
    return path

def load_draft(path: str | Path) -> dict:
    """Load a draft JSON by path (string or Path)."""
    return _read_json(Path(path), {})
