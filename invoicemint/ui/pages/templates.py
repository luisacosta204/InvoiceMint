# invoicemint/ui/pages/templates.py
import tkinter as tk
from tkinter import ttk


class TemplatesPage(ttk.Frame):
    """
    Placeholder for:
    - Built-in template gallery
    - Upload your own template (HTML/DOCX)
    - Later: preview & select default
    """
    def __init__(self, parent, tokens):
        super().__init__(parent, style="Card.TFrame")
        self.tokens = tokens
        self._build()

    def restyle(self, tokens):
        self.tokens = tokens

    def _build(self):
        ttk.Label(self, text="Templates", font=("Montserrat", 16, "bold")).grid(
            row=0, column=0, sticky="w", padx=12, pady=12
        )
        ttk.Label(
            self,
            text="Coming soon: Built-in templates and Upload Your Own (HTML/DOCX) with preview.",
        ).grid(row=1, column=0, sticky="w", padx=12)
