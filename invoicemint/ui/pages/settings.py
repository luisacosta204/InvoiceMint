# invoicemint/ui/pages/settings.py
import tkinter as tk
from tkinter import ttk

from invoicemint.services.storage import load_settings, save_settings


class SettingsPage(ttk.Frame):
    """
    Basic settings placeholder:
    - Theme info lives on the topbar toggle
    - Later: company profile, logo, currency, tax presets
    """
    def __init__(self, parent, tokens):
        super().__init__(parent, style="Card.TFrame")
        self.tokens = tokens
        self.settings = load_settings()
        self._build()

    def restyle(self, tokens):
        self.tokens = tokens

    def _build(self):
        ttk.Label(self, text="Settings", font=("Montserrat", 16, "bold")).grid(
            row=0, column=0, sticky="w", padx=12, pady=12
        )
        ttk.Label(
            self,
            text="Theme toggles from the top bar. Coming soon: company info, currency, tax presets, and backups.",
        ).grid(row=1, column=0, sticky="w", padx=12)
