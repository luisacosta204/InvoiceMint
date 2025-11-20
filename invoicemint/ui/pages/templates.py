import customtkinter as ctk

class TemplatesPage(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, corner_radius=16)
        ctk.CTkLabel(self, text="Templates", font=("Segoe UI", 18, "bold")).pack(anchor="w", padx=16, pady=(16, 6))
        box = ctk.CTkFrame(self, corner_radius=12)
        box.pack(fill="both", expand=True, padx=16, pady=16)
        ctk.CTkLabel(box, text="Coming soon: built-in templates and “Upload your own” (HTML/DOCX) with preview.").pack(padx=16, pady=16, anchor="w")
