1. Requirements

Git for Windows → https://git-scm.com/download/win

Python 3.x (add to PATH during install)

VS Code + Python extension

2. Clone the repo
cd %USERPROFILE%\Documents\projects
git clone git@github.com:<your-username>/InvoiceMint.git
cd InvoiceMint

Use HTTPS instead if SSH isn’t set up: git clone https://github.com/<your-username>/InvoiceMint.git

3. Create and activate virtual environment
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip

If you have dependencies:

pip install -r requirements.txt
4. Run the app
python -m invoicemint.app
5. Optional VS Code setup

Select interpreter: Ctrl+Shift+P → Python: Select Interpreter → choose .venv

Optional .vscode/launch.json:

{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Run InvoiceMint",
      "type": "python",
      "request": "launch",
      "module": "invoicemint.app",
      "console": "integratedTerminal"
    }
  ]
}
6. Git workflow
git add -A
git commit -m "Describe change"
git push

To sync on the other machine:

git pull
7. Build executable (later)
pip install pyinstaller
pyinstaller --onefile --windowed -n InvoiceMint --add-data "assets;assets" invoicemint/app.py
8. Add SSH key (optional)
ssh-keygen -t ed25519 -C "your_email@example.com"
cat ~/.ssh/id_ed25519.pub

Add key at https://github.com/settings/keys → test: