# invoicemint/ui/pages/clients.py
import tkinter as tk
from tkinter import ttk

from invoicemint.services.storage import load_clients, save_clients


class ClientsPage(ttk.Frame):
    """
    Simple client manager:
    - Add a client (name, email, address)
    - Persist to local JSON
    """
    def __init__(self, parent, tokens):
        super().__init__(parent, style="Card.TFrame")
        self.tokens = tokens
        self.clients = load_clients()
        self._build()

    def restyle(self, tokens):
        self.tokens = tokens

    def _build(self):
        self.grid_columnconfigure(0, weight=1)
        ttk.Label(self, text="Clients", font=("Montserrat", 16, "bold")).grid(
            row=0, column=0, sticky="w", padx=12, pady=(12, 0)
        )

        # quick add row
        row = ttk.Frame(self, style="Card.TFrame")
        row.grid(row=1, column=0, sticky="ew", padx=12, pady=8)

        self.e_name = ttk.Entry(row, width=24)
        self.e_email = ttk.Entry(row, width=28)
        self.e_addr = ttk.Entry(row, width=40)

        for i, (lbl, w) in enumerate([
            ("Name", self.e_name),
            ("Email", self.e_email),
            ("Address", self.e_addr),
        ]):
            ttk.Label(row, text=lbl).grid(row=0, column=i*2, sticky="w", padx=(0, 4))
            w.grid(row=0, column=i*2+1, padx=(0, 8))

        ttk.Button(row, text="Add", command=self.add_client).grid(row=0, column=6)

        # table
        self.tree = ttk.Treeview(
            self, columns=("name", "email", "addr"), show="headings", height=12
        )
        for col, text, w in [("name", "Name", 200), ("email", "Email", 240), ("addr", "Address", 360)]:
            self.tree.heading(col, text=text)
            self.tree.column(col, width=w, anchor="w")
        self.tree.grid(row=2, column=0, sticky="nsew", padx=12, pady=(0, 12))
        self.grid_rowconfigure(2, weight=1)

        for c in self.clients:
            self.tree.insert("", tk.END, values=(c.get("name", ""), c.get("email", ""), c.get("address", "")))

    def add_client(self):
        name = self.e_name.get().strip()
        email = self.e_email.get().strip()
        addr = self.e_addr.get().strip()
        if not name:
            return
        self.clients.append({"name": name, "email": email, "address": addr})
        save_clients(self.clients)
        self.tree.insert("", tk.END, values=(name, email, addr))
        self.e_name.delete(0, tk.END); self.e_email.delete(0, tk.END); self.e_addr.delete(0, tk.END)
