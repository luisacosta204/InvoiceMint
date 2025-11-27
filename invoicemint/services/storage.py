# invoicemint/services/storage.py
import json
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
    Path(path).write_text(json.dumps(data, indent=2), encoding="utf-8")


# ---------- Settings & Clients ----------
DEFAULT_SETTINGS = {
    "theme": "light",
    "company": {},
    "pdf": {
        "template": "Minimal",  # default PDF template
    },
    "default_notes": "Thank you for your business!\nPayment is due in 14 days.",
}


def load_settings():
    data = _read_json(SETTINGS_FILE, DEFAULT_SETTINGS)

    # merge top-level
    merged = DEFAULT_SETTINGS.copy()
    merged.update(data or {})

    # merge nested pdf dict
    pdf_cfg = DEFAULT_SETTINGS.get("pdf", {}).copy()
    pdf_cfg.update((data or {}).get("pdf", {}) or {})
    merged["pdf"] = pdf_cfg

    return merged


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


def delete_draft(path_or_name: str) -> bool:
    """
    Delete a draft file by full path or just filename.
    Returns True on success, False if file wasn't removed.
    """
    p = Path(path_or_name)
    # If they passed just the filename, look in DRAFTS_DIR
    if not p.is_absolute():
        p = DRAFTS_DIR / p

    try:
        if p.exists():
            p.unlink()
            return True
    except Exception:
        return False
    return False


def rename_draft(path_or_name: str, new_name: str) -> Path | None:
    """
    Rename a draft file.

    path_or_name: existing full path or filename
    new_name: new base name (with or without .json)

    Returns the new Path on success, or None on failure.
    """
    if not new_name:
        return None

    src = Path(path_or_name)
    if not src.is_absolute():
        src = DRAFTS_DIR / src

    if not src.exists():
        return None

    # Ensure .json extension
    filename = new_name if new_name.endswith(".json") else f"{new_name}.json"
    dest = src.with_name(filename)

    try:
        src.rename(dest)
        return dest
    except Exception:
        return None
