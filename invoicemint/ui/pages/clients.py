import customtkinter as ctk
import tkinter as tk
from invoicemint.services.storage import load_clients, save_clients


class ClientsPage(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, corner_radius=16)
        self.clients = load_clients() or []
        self.filtered_clients = list(self.clients)

        self.search_var = tk.StringVar(value="")
        self._build()

    def _build(self):
        # Layout: header row, form row, list row
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        header_row = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        header_row.grid(row=0, column=0, sticky="ew", padx=16, pady=(16, 6))
        header_row.grid_columnconfigure(1, weight=1)

        header = ctk.CTkLabel(header_row, text="Clients", font=("Segoe UI", 18, "bold"))
        header.grid(row=0, column=0, sticky="w")

        # Search box
        search = ctk.CTkEntry(
            header_row,
            textvariable=self.search_var,
            placeholder_text="Search clients (name, email, address)…",
            width=360,
        )
        search.grid(row=0, column=1, sticky="e", padx=(12, 0))
        search.bind("<KeyRelease>", self._on_search)

        # Form row
        form = ctk.CTkFrame(self, corner_radius=12)
        form.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 8))
        form.grid_columnconfigure((0, 1, 2), weight=1)

        self.e_name = ctk.CTkEntry(form, placeholder_text="Name")
        self.e_email = ctk.CTkEntry(form, placeholder_text="Email")
        self.e_addr = ctk.CTkEntry(form, placeholder_text="Address")

        add_btn = ctk.CTkButton(form, text="Add", width=90, command=self.add_client)

        self.e_name.grid(row=0, column=0, padx=6, pady=10, sticky="ew")
        self.e_email.grid(row=0, column=1, padx=6, pady=10, sticky="ew")
        self.e_addr.grid(row=0, column=2, padx=6, pady=10, sticky="ew")
        add_btn.grid(row=0, column=3, padx=6, pady=10)

        # List
        self.list_frame = ctk.CTkScrollableFrame(self, corner_radius=12)
        self.list_frame.grid(row=2, column=0, sticky="nsew", padx=16, pady=(0, 16))

        self._render_list()

    # -------------------------
    # Search / filtering
    # -------------------------
    def _matches(self, client: dict, q: str) -> bool:
        if not q:
            return True
        q = q.lower().strip()

        name = str(client.get("name", "")).lower()
        email = str(client.get("email", "")).lower()
        addr = str(client.get("address", "")).lower()

        # simple contains; we can upgrade to fuzzy later
        return (q in name) or (q in email) or (q in addr)

    def _on_search(self, *_):
        q = (self.search_var.get() or "").strip()
        self.filtered_clients = [c for c in self.clients if self._matches(c, q)]
        self._render_list()

    # -------------------------
    # Rendering
    # -------------------------
    def _clear_list(self):
        for w in self.list_frame.winfo_children():
            w.destroy()

    def _render_list(self):
        self._clear_list()
        for c in self.filtered_clients:
            self._add_list_row(c)

    def _add_list_row(self, c):
        row = ctk.CTkFrame(self.list_frame, corner_radius=8)
        row.pack(fill="x", padx=6, pady=6)

        name = c.get("name", "")
        email = c.get("email", "")
        addr = c.get("address", "")

        ctk.CTkLabel(row, text=name, width=180, anchor="w").pack(side="left", padx=10, pady=10)
        ctk.CTkLabel(row, text=email, width=220, anchor="w").pack(side="left", padx=10, pady=10)
        ctk.CTkLabel(row, text=addr, anchor="w").pack(side="left", padx=10, pady=10)

    # -------------------------
    # Add
    # -------------------------
    def add_client(self):
        name = self.e_name.get().strip()
        email = self.e_email.get().strip()
        addr = self.e_addr.get().strip()
        if not name:
            return

        obj = {"name": name, "email": email, "address": addr}
        self.clients.append(obj)
        save_clients(self.clients)

        # Clear inputs
        self.e_name.delete(0, tk.END)
        self.e_email.delete(0, tk.END)
        self.e_addr.delete(0, tk.END)

        # Re-filter using current search text so list stays consistent
        self._on_search()
