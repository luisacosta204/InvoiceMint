# invoicemint/ui/main_ui.py
import tkinter as tk
from tkinter import ttk

from invoicemint.theme.tokens import TOKENS_LIGHT, TOKENS_DARK
from invoicemint.ui.pages.invoice_builder import InvoiceBuilder
from invoicemint.ui.pages.clients import ClientsPage
from invoicemint.ui.pages.templates import TemplatesPage
from invoicemint.ui.pages.settings import SettingsPage
from invoicemint.services.storage import load_settings, save_settings


class MainApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("InvoiceMint — Prototype")
        self.minsize(1080, 720)

        # load settings + theme
        self.settings = load_settings() or {"theme": "light", "company": {}}
        self.dark = self.settings.get("theme", "light") == "dark"
        self.tokens = TOKENS_DARK if self.dark else TOKENS_LIGHT

        self._init_style()
        self._build_layout()
        self.show_page("invoice")  # start on Invoice Builder

    # -------------- styles / theme --------------
    def _init_style(self):
        t = self.tokens
        style = ttk.Style()
        style.theme_use("clam")

        # root background
        style.configure("App.TFrame", background=t["color"]["bg"])

        # panels / cards
        style.configure("Card.TFrame", background=t["color"]["surface"])

        # labels inside cards
        style.configure(
            "TLabel",
            background=t["color"]["surface"],
            foreground=t["color"]["text"],
        )

        # sidebar
        style.configure("Sidebar.TFrame", background=t["color"]["surface"])
        style.configure("Sidebar.TButton", padding=8)

        # buttons
        style.configure(
            "Accent.TButton",
            padding=10,
            background=t["color"]["accent"],
            foreground=t["color"]["accent_text"],
        )
        style.map("Accent.TButton", background=[("active", t["color"]["accent"])])

        # window bg
        self.configure(bg=t["color"]["bg"])

    def toggle_theme(self):
        self.dark = not self.dark
        self.settings["theme"] = "dark" if self.dark else "light"
        save_settings(self.settings)
        self.tokens = TOKENS_DARK if self.dark else TOKENS_LIGHT
        self._init_style()

        # repaint top-level frames
        self.sidebar.configure(style="Sidebar.TFrame")
        self.topbar.configure(style="Card.TFrame")
        self.content_wrap.configure(style="App.TFrame")

        # allow current page to react if needed
        if hasattr(self.current_page, "restyle"):
            self.current_page.restyle(self.tokens)

    # -------------- layout --------------
    def _build_layout(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # top bar
        self.topbar = ttk.Frame(self, style="Card.TFrame")
        self.topbar.grid(row=0, column=0, columnspan=2, sticky="ew", padx=(16, 16), pady=(16, 8))
        ttk.Label(
            self.topbar, text="InvoiceMint", font=("Montserrat", 18, "bold"),
            background=self.tokens["color"]["surface"]
        ).grid(row=0, column=0, sticky="w")
        ttk.Button(self.topbar, text="Toggle Theme", command=self.toggle_theme).grid(row=0, column=1, sticky="e")
        self.topbar.grid_columnconfigure(0, weight=1)

        # sidebar
        self.sidebar = ttk.Frame(self, style="Sidebar.TFrame")
        self.sidebar.grid(row=1, column=0, sticky="nsw", padx=(16, 8), pady=(0, 16))

        for i, (label, key) in enumerate([
            ("Dashboard", "invoice"),
            ("Clients", "clients"),
            ("Templates", "templates"),
            ("Settings", "settings"),
        ]):
            ttk.Button(self.sidebar, text=label, style="Sidebar.TButton",
                       command=lambda k=key: self.show_page(k)).grid(row=i, column=0, sticky="ew", pady=6)

        # content area
        self.content_wrap = ttk.Frame(self, style="App.TFrame")
        self.content_wrap.grid(row=1, column=1, sticky="nsew", padx=(0, 16), pady=(0, 16))
        self.content_wrap.grid_columnconfigure(0, weight=1)
        self.content_wrap.grid_rowconfigure(0, weight=1)

        self.current_page = None

    # -------------- routing --------------
    def show_page(self, key: str):
        if self.current_page is not None:
            self.current_page.destroy()

        if key == "invoice":
            self.current_page = InvoiceBuilder(self.content_wrap, self.tokens)
        elif key == "clients":
            self.current_page = ClientsPage(self.content_wrap, self.tokens)
        elif key == "templates":
            self.current_page = TemplatesPage(self.content_wrap, self.tokens)
        elif key == "settings":
            self.current_page = SettingsPage(self.content_wrap, self.tokens)
        else:
            self.current_page = ttk.Frame(self.content_wrap, style="Card.TFrame")

        self.current_page.grid(row=0, column=0, sticky="nsew")
