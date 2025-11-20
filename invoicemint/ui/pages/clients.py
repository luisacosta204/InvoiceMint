import customtkinter as ctk
import tkinter as tk
from invoicemint.services.storage import load_clients, save_clients


class ClientsPage(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, corner_radius=16)
        self.clients = load_clients()
        self._build()

    def _build(self):
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        header = ctk.CTkLabel(self, text="Clients", font=("Segoe UI", 18, "bold"))
        header.grid(row=0, column=0, sticky="w", padx=16, pady=(16, 6))

        form = ctk.CTkFrame(self, corner_radius=12)
        form.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 8))
        form.grid_columnconfigure((0,1,2,3,4), weight=1)
        self.e_name = ctk.CTkEntry(form, placeholder_text="Name")
        self.e_email = ctk.CTkEntry(form, placeholder_text="Email")
        self.e_addr = ctk.CTkEntry(form, placeholder_text="Address")
        add_btn = ctk.CTkButton(form, text="Add", width=90, command=self.add_client)
        self.e_name.grid(row=0, column=0, padx=6, pady=10, sticky="ew")
        self.e_email.grid(row=0, column=1, padx=6, pady=10, sticky="ew")
        self.e_addr.grid(row=0, column=2, padx=6, pady=10, sticky="ew")
        add_btn.grid(row=0, column=3, padx=6, pady=10)

        # list
        self.list_frame = ctk.CTkScrollableFrame(self, corner_radius=12)
        self.list_frame.grid(row=2, column=0, sticky="nsew", padx=16, pady=(0, 16))
        for c in self.clients:
            self._add_list_row(c)

    def _add_list_row(self, c):
        row = ctk.CTkFrame(self.list_frame, corner_radius=8)
        row.pack(fill="x", padx=6, pady=6)
        name = c.get("name",""); email = c.get("email",""); addr = c.get("address","")
        ctk.CTkLabel(row, text=name).pack(side="left", padx=10, pady=10)
        ctk.CTkLabel(row, text=email).pack(side="left", padx=10, pady=10)
        ctk.CTkLabel(row, text=addr).pack(side="left", padx=10, pady=10)

    def add_client(self):
        name = self.e_name.get().strip()
        email = self.e_email.get().strip()
        addr = self.e_addr.get().strip()
        if not name:
            return
        obj = {"name": name, "email": email, "address": addr}
        self.clients.append(obj)
        save_clients(self.clients)
        self._add_list_row(obj)
        self.e_name.delete(0, tk.END); self.e_email.delete(0, tk.END); self.e_addr.delete(0, tk.END)
