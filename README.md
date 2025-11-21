# InvoiceMint

**InvoiceMint** is a clean, modern, cross-platform invoicing and quoting tool built in Python. It’s designed to feel professional yet simple, so freelancers and small businesses can create beautiful invoices and quotes in minutes—without the clutter of large accounting software.

---

## Overview

* Built with **Python + Tkinter** (desktop-native GUI)
* Works seamlessly on **macOS** and **Windows**
* Easy to package into a single executable (`.exe` or `.app`)
* Local-first, privacy-friendly (no cloud dependency)
* Simple JSON storage for clients, settings, and drafts

---

## Features

* Invoice & Quote Builder — Add line items, quantities, and taxes with real-time totals
* Client Manager — Save and reuse client details locally
* Template System (coming soon) — Built-in and custom HTML/DOCX templates
* Save & Load Drafts (planned) — Keep unfinished work for later editing
* Export to PDF (planned) — Generate professional PDFs for clients
* Light/Dark Themes — Modern, readable interface in both modes
* Offline-First Design — All data stays on your computer

---

## Running the App

Run from the project root (the folder containing `invoicemint/`):

### macOS

```bash
python3 -m invoicemint.app
```

### Windows

```powershell
python -m invoicemint.app
```

The main window will open with the sidebar (Dashboard, Clients, Templates, Settings) and the Invoice Builder as the default page.

---

## Development Setup

### Windows

Follow [WINDOWS_SETUP.md](WINDOWS_SETUP.md) for full instructions.

### macOS

Follow [MAC_SETUP.md](MAC_SETUP.md) for full instructions.

Both guides include steps for:

* Virtual environment setup
* Dependency installation
* Running the app
* VS Code interpreter selection
* Optional PyInstaller build commands

---

## Folder Structure

```
InvoiceMintProject/
├── .venv/                    # Virtual environment
├── invoicemint/              # Main package
│   ├── app.py                # Entry point
│   ├── ui/                   # GUI logic
│   ├── services/             # Storage, persistence, helpers
│   ├── theme/                # Design tokens and style config
│   ├── assets/               # Templates and static assets
│   └── __init__.py
├── MAC_SETUP.md
├── WINDOWS_SETUP.md
├── requirements.txt
└── README.md
```

---

## Building Executables

### macOS

```bash
pyinstaller --onefile --windowed -n InvoiceMint --add-data "assets:assets" invoicemint/app.py
```

Output: `dist/InvoiceMint`

### Windows

```powershell
pyinstaller --onefile --windowed -n InvoiceMint --add-data "assets;assets" invoicemint/app.py
```

Output: `dist/InvoiceMint.exe`

---

## Git Workflow

```bash
git add -A
git commit -m "Describe change"
git push
# On other machine
git pull
```
## Quick Push to GitHub
Use the helper script to commit and push all recent changes in one step:

```bash
python quickpush.py "Describe your update"
# or (macOS/Linux)
./quickpush.py "Describe your update"
---

## Coming Soon

* PDF export (via ReportLab)
* Customizable templates (HTML + DOCX)
* Invoice numbering & date tracking
* Multi-currency support
* Settings for company info & logo

---

## License

You can add a license of your choice later (MIT, Apache, etc.). For now, this project is private and intended for development use only.

---

### Made with Python
