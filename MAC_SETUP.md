1. Requirements

Python 3.x → https://www.python.org/downloads/

VS Code + Python extension

Git (use brew install git if needed)

2. Clone the repo
cd ~/Documents/projects
git clone git@github.com:<your-username>/InvoiceMint.git
cd InvoiceMint

Or HTTPS: git clone https://github.com/<your-username>/InvoiceMint.git

3. Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip

If you have dependencies:

pip install -r requirements.txt
4. Run the app
python3 -m invoicemint.app
# or
python invoicemint/app.py
5. Optional VS Code setup

Interpreter: ⌘⇧P → Python: Select Interpreter → choose .venv

Optional .vscode/settings.json:

{
  "python.defaultInterpreterPath": "${workspaceFolder}/.venv/bin/python",
  "python.analysis.extraPaths": [
    "${workspaceFolder}",
    "${workspaceFolder}/invoicemint"
  ],
  "python.analysis.indexing": true
}

Optional .vscode/launch.json: same as Windows.

6. Git workflow
git add -A
git commit -m "Describe change"
git push

To sync on the other machine:

git pull
7. Build Mac app (later)
pip install pyinstaller
pyinstaller --onefile --windowed -n InvoiceMint --add-data "assets:assets" invoicemint/app.py
8. Add SSH key (optional)
ssh-keygen -t ed25519 -C "your_email@example.com"
cat ~/.ssh/id_ed25519.pub

Add at https://github.com/settings/keys → test:

ssh -T git@github.com