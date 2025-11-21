# invoicemint/ui/pages/settings.py
import customtkinter as ctk
from tkinter import filedialog
from invoicemint.services.storage import load_settings, save_settings


class SettingsPage(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, corner_radius=16)
        self.settings = load_settings() or {"theme": "light", "company": {}}
        self.company = self.settings.get("company", {})
        self._build()

    def _build(self):
        ctk.CTkLabel(self, text="Settings", font=("Segoe UI", 18, "bold")).pack(
            anchor="w", padx=16, pady=(16, 6)
        )

        # Appearance
        card_theme = ctk.CTkFrame(self, corner_radius=12)
        card_theme.pack(fill="x", padx=16, pady=(0, 16))
        ctk.CTkLabel(card_theme, text="Appearance").grid(
            row=0, column=0, padx=12, pady=12, sticky="w"
        )
        mode = "Dark" if self.settings.get("theme") == "dark" else "Light"
        self.mode_var = ctk.StringVar(value=mode)
        self.mode_input = ctk.CTkOptionMenu(
            card_theme,
            values=["Light", "Dark", "System"],
            variable=self.mode_var,
            command=self._apply_theme,
        )
        self.mode_input.grid(row=0, column=1, padx=12, pady=12, sticky="w")

        # Company
        card_co = ctk.CTkFrame(self, corner_radius=12)
        card_co.pack(fill="x", padx=16, pady=(0, 16))

        def entry(row, label, key, placeholder=""):
            ctk.CTkLabel(card_co, text=label).grid(
                row=row, column=0, padx=12, pady=8, sticky="e"
            )
            var = ctk.StringVar(value=self.company.get(key, ""))
            ent = ctk.CTkEntry(
                card_co, textvariable=var, placeholder_text=placeholder, width=360
            )
            ent.grid(row=row, column=1, padx=12, pady=8, sticky="w")
            return var

        self.name_var = entry(0, "Company Name", "name", "Your LLC")
        self.addr_var = entry(1, "Address", "address", "Street, City, State")
        self.email_var = entry(2, "Email", "email", "you@company.com")
        self.phone_var = entry(3, "Phone", "phone", "(555) 123-4567")

        ctk.CTkLabel(card_co, text="Logo").grid(
            row=4, column=0, padx=12, pady=8, sticky="e"
        )
        self.logo_var = ctk.StringVar(value=self.company.get("logo_path", ""))
        logo_row = ctk.CTkFrame(card_co, corner_radius=8)
        logo_row.grid(row=4, column=1, padx=12, pady=8, sticky="w")
        ctk.CTkEntry(
            logo_row, textvariable=self.logo_var, width=300, placeholder_text="Path to logo image"
        ).pack(side="left", padx=(0, 8))
        ctk.CTkButton(logo_row, text="Browse", width=90, command=self._pick_logo).pack(
            side="left"
        )

        # Save button
        ctk.CTkButton(self, text="Save Settings", command=self._save).pack(
            anchor="e", padx=16, pady=(0, 16)
        )

    def _pick_logo(self):
        path = filedialog.askopenfilename(
            title="Select Logo",
            filetypes=[("Images", "*.png;*.jpg;*.jpeg;*.gif;*.bmp")],
        )
        if path:
            self.logo_var.set(path)

    def _apply_theme(self, value):
        if value == "System":
            ctk.set_appearance_mode("System")
        else:
            ctk.set_appearance_mode(value)
        self.settings["theme"] = (
            "dark"
            if value == "Dark"
            else ("light" if value == "Light" else self.settings.get("theme"))
        )

    def _save(self):
        self.company["name"] = self.name_var.get().strip()
        self.company["address"] = self.addr_var.get().strip()
        self.company["email"] = self.email_var.get().strip()
        self.company["phone"] = self.phone_var.get().strip()
        self.company["logo_path"] = self.logo_var.get().strip()
        self.settings["company"] = self.company
        save_settings(self.settings)

        toast = ctk.CTkToplevel(self)
        toast.title("Saved")
        ctk.CTkLabel(toast, text="Settings saved").pack(padx=16, pady=16)
        toast.geometry("+%d+%d" % (self.winfo_rootx() + 120, self.winfo_rooty() + 80))
        toast.after(1400, toast.destroy)
