# invoicemint/ui/pages/settings.py
import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog

from invoicemint.services.storage import load_settings, save_settings


class SettingsPage(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, corner_radius=16)
        self.settings = load_settings() or {}
        self.company = self.settings.get("company") or {}
        self.pdf_cfg = self.settings.get("pdf") or {}

        self.theme_var = tk.StringVar(
            value="dark" if self.settings.get("theme") == "dark" else "light"
        )
        self.company_name_var = tk.StringVar(value=self.company.get("name", ""))
        self.company_address_var = tk.StringVar(value=self.company.get("address", ""))
        self.company_email_var = tk.StringVar(value=self.company.get("email", ""))
        self.company_phone_var = tk.StringVar(value=self.company.get("phone", ""))
        self.company_website_var = tk.StringVar(value=self.company.get("website", ""))
        self.logo_path_var = tk.StringVar(value=self.company.get("logo_path", ""))

        self.pdf_template_var = tk.StringVar(
            value=self.pdf_cfg.get("template", "Minimal")
        )

        self.default_notes_text = None  # will be CTkTextbox

        self._build()

    def _build(self):
        self.grid_rowconfigure(3, weight=1)
        self.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(
            self,
            text="Settings",
            font=("Segoe UI", 20, "bold"),
        )
        title.grid(row=0, column=0, sticky="w", padx=16, pady=(16, 8))

        # ---- THEME CARD ----
        theme_card = ctk.CTkFrame(self, corner_radius=12)
        theme_card.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 8))

        ctk.CTkLabel(
            theme_card, text="Appearance", font=("Segoe UI", 14, "bold")
        ).grid(row=0, column=0, padx=12, pady=(10, 4), sticky="w")
        ctk.CTkLabel(
            theme_card,
            text="Switch between light and dark mode.",
            font=("Segoe UI", 11),
        ).grid(row=1, column=0, padx=12, pady=(0, 8), sticky="w")

        theme_switch = ctk.CTkSegmentedButton(
            theme_card,
            values=["Light", "Dark"],
            variable=self.theme_var,
            command=self._on_theme_change,
        )
        theme_switch.grid(row=0, column=1, rowspan=2, padx=12, pady=10, sticky="e")

        theme_card.grid_columnconfigure(0, weight=1)
        theme_card.grid_columnconfigure(1, weight=0)

        # ---- COMPANY CARD ----
        company_card = ctk.CTkFrame(self, corner_radius=12)
        company_card.grid(row=2, column=0, sticky="ew", padx=16, pady=(0, 8))

        ctk.CTkLabel(
            company_card, text="Company Profile", font=("Segoe UI", 14, "bold")
        ).grid(row=0, column=0, columnspan=4, padx=12, pady=(10, 4), sticky="w")

        # Name
        ctk.CTkLabel(company_card, text="Name").grid(
            row=1, column=0, padx=12, pady=(6, 4), sticky="e"
        )
        ctk.CTkEntry(company_card, textvariable=self.company_name_var, width=260).grid(
            row=1, column=1, padx=(0, 16), pady=(6, 4), sticky="w"
        )

        # Email
        ctk.CTkLabel(company_card, text="Email").grid(
            row=2, column=0, padx=12, pady=4, sticky="e"
        )
        ctk.CTkEntry(company_card, textvariable=self.company_email_var, width=260).grid(
            row=2, column=1, padx=(0, 16), pady=4, sticky="w"
        )

        # Phone
        ctk.CTkLabel(company_card, text="Phone").grid(
            row=3, column=0, padx=12, pady=4, sticky="e"
        )
        ctk.CTkEntry(company_card, textvariable=self.company_phone_var, width=260).grid(
            row=3, column=1, padx=(0, 16), pady=4, sticky="w"
        )

        # Website
        ctk.CTkLabel(company_card, text="Website").grid(
            row=4, column=0, padx=12, pady=4, sticky="e"
        )
        ctk.CTkEntry(
            company_card, textvariable=self.company_website_var, width=260
        ).grid(row=4, column=1, padx=(0, 16), pady=4, sticky="w")

        # Address (span)
        ctk.CTkLabel(company_card, text="Address").grid(
            row=5, column=0, padx=12, pady=4, sticky="ne"
        )
        addr_box = ctk.CTkTextbox(company_card, height=60, width=260)
        addr_box.grid(row=5, column=1, padx=(0, 16), pady=4, sticky="w")
        addr_box.insert("1.0", self.company_address_var.get())
        self.address_box = addr_box  # keep ref

        # Logo
        ctk.CTkLabel(company_card, text="Logo").grid(
            row=1, column=2, padx=12, pady=(6, 4), sticky="e"
        )
        logo_entry = ctk.CTkEntry(
            company_card, textvariable=self.logo_path_var, width=220
        )
        logo_entry.grid(row=1, column=3, padx=(0, 8), pady=(6, 4), sticky="w")

        ctk.CTkButton(
            company_card,
            text="Browse…",
            width=90,
            command=self._pick_logo,
        ).grid(row=1, column=4, padx=(0, 12), pady=(6, 4), sticky="w")

        for col in range(5):
            company_card.grid_columnconfigure(col, weight=0)
        company_card.grid_columnconfigure(1, weight=1)

        # ---- PDF TEMPLATE + DEFAULT NOTES CARD ----
        pdf_card = ctk.CTkFrame(self, corner_radius=12)
        pdf_card.grid(row=3, column=0, sticky="nsew", padx=16, pady=(0, 8))
        pdf_card.grid_columnconfigure(0, weight=1)
        pdf_card.grid_columnconfigure(1, weight=0)

        ctk.CTkLabel(
            pdf_card, text="PDF & Invoice Defaults", font=("Segoe UI", 14, "bold")
        ).grid(row=0, column=0, columnspan=2, padx=12, pady=(10, 4), sticky="w")

        # Template selector
        ctk.CTkLabel(pdf_card, text="PDF Template").grid(
            row=1, column=0, padx=12, pady=6, sticky="w"
        )
        tmpl_menu = ctk.CTkOptionMenu(
            pdf_card,
            values=["Modern", "Compact", "Minimal"],
            variable=self.pdf_template_var,
        )
        tmpl_menu.grid(row=1, column=1, padx=12, pady=6, sticky="e")

        # Default notes
        ctk.CTkLabel(pdf_card, text="Default Invoice Notes").grid(
            row=2, column=0, padx=12, pady=(10, 4), sticky="w"
        )

        self.default_notes_text = ctk.CTkTextbox(pdf_card, height=100)
        self.default_notes_text.grid(
            row=3, column=0, columnspan=2, padx=12, pady=(0, 10), sticky="nsew"
        )
        self.default_notes_text.insert(
            "1.0",
            self.settings.get(
                "default_notes",
                "Thank you for your business!\nPayment is due in 14 days.",
            ),
        )

        # ---- SAVE BUTTON ----
        save_bar = ctk.CTkFrame(self, fg_color="transparent")
        save_bar.grid(row=4, column=0, sticky="e", padx=16, pady=(0, 16))

        save_btn = ctk.CTkButton(
            save_bar,
            text="Save Settings",
            width=140,
            command=self._on_save,
        )
        save_btn.pack(side="right", padx=4, pady=4)

    # --------- callbacks ----------

    def _on_theme_change(self, *_):
        mode = self.theme_var.get()
        self.settings["theme"] = "dark" if mode.lower() == "dark" else "light"
        # Do not call ctk.set_appearance_mode here to avoid fighting with main app;
        # MainApp already handles theme toggle. This just stores preference.

    def _pick_logo(self):
        path = filedialog.askopenfilename(
            title="Select Logo Image",
            filetypes=[
                ("Image files", "*.png;*.jpg;*.jpeg;*.gif;*.bmp"),
                ("All files", "*.*"),
            ],
        )
        if not path:
            return
        self.logo_path_var.set(path)

    def _on_save(self):
        # sync address back from textbox
        self.company_address_var.set(self.address_box.get("1.0", "end").strip())

        # rebuild company dict
        self.company = {
            "name": self.company_name_var.get().strip(),
            "address": self.company_address_var.get().strip(),
            "email": self.company_email_var.get().strip(),
            "phone": self.company_phone_var.get().strip(),
            "website": self.company_website_var.get().strip(),
            "logo_path": self.logo_path_var.get().strip(),
        }

        # pdf config
        self.pdf_cfg = {
            "template": self.pdf_template_var.get() or "Minimal",
        }

        # default notes
        default_notes = (
            self.default_notes_text.get("1.0", "end").rstrip("\n")
        )

        # update settings dict
        self.settings["company"] = self.company
        self.settings["pdf"] = self.pdf_cfg
        self.settings["default_notes"] = default_notes

        save_settings(self.settings)

        # tiny toast
        toast = ctk.CTkToplevel(self)
        toast.title("Saved")
        ctk.CTkLabel(toast, text="Settings saved.").pack(padx=16, pady=16)
        toast.geometry(
            "+%d+%d" % (self.winfo_rootx() + 120, self.winfo_rooty() + 80)
        )
        toast.after(1500, toast.destroy)
