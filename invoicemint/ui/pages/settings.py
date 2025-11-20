import customtkinter as ctk
from invoicemint.services.storage import load_settings, save_settings


class SettingsPage(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, corner_radius=16)
        self.settings = load_settings() or {"theme": "light", "company": {}}
        self._build()

    def _build(self):
        ctk.CTkLabel(self, text="Settings", font=("Segoe UI", 18, "bold")).pack(anchor="w", padx=16, pady=(16, 6))

        card = ctk.CTkFrame(self, corner_radius=12)
        card.pack(fill="x", padx=16, pady=(0, 16))

        # Theme selector
        ctk.CTkLabel(card, text="Appearance").grid(row=0, column=0, padx=12, pady=12, sticky="w")
        mode = "Dark" if self.settings.get("theme") == "dark" else "Light"
        self.mode_var = ctk.StringVar(value=mode)
        self.mode_input = ctk.CTkOptionMenu(card, values=["Light", "Dark", "System"], variable=self.mode_var,
                                            command=self._apply_theme)
        self.mode_input.grid(row=0, column=1, padx=12, pady=12, sticky="w")

        # Company card placeholder
        company = ctk.CTkFrame(self, corner_radius=12)
        company.pack(fill="x", padx=16, pady=(0, 16))
        ctk.CTkLabel(company, text="Company profile (coming soon)").pack(anchor="w", padx=12, pady=12)

    def _apply_theme(self, value):
        if value == "System":
            ctk.set_appearance_mode("System")
        else:
            ctk.set_appearance_mode(value)
        self.settings["theme"] = "dark" if value == "Dark" else ("light" if value == "Light" else self.settings.get("theme"))
        save_settings(self.settings)
