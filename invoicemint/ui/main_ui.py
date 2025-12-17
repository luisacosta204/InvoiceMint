# Modern shell using CustomTkinter
import customtkinter as ctk
from invoicemint.ui.pages.invoice_builder import InvoiceBuilder
from invoicemint.ui.pages.clients import ClientsPage
from invoicemint.ui.pages.templates import TemplatesPage
from invoicemint.ui.pages.settings import SettingsPage
from invoicemint.services.storage import load_settings, save_settings, list_drafts, load_draft
from invoicemint.ui.pages.history import DraftsHistory
from invoicemint.ui.pages.dashboard import DashboardPage


class MainApp(ctk.CTk):  # App window
    def __init__(self):
        super().__init__()
        self.title("InvoiceMint — Prototype")
        self.minsize(1120, 720)

        # settings + theme
        self.settings = load_settings() or {"theme": "light", "company": {}}
        ctk.set_appearance_mode("Dark" if self.settings.get("theme") == "dark" else "Light")

        # grid
        self.grid_columnconfigure(1, weight=1)  # content grows
        self.grid_rowconfigure(1, weight=1)

        # top bar
        self._build_topbar()

        # sidebar
        self._build_sidebar()

        # content container
        self.content = ctk.CTkFrame(self, fg_color=("white", "#0e1116"))
        self.content.grid(row=1, column=1, sticky="nsew", padx=(0, 16), pady=(0, 16))
        self.content.grid_rowconfigure(0, weight=1)
        self.content.grid_columnconfigure(0, weight=1)

        self.current_page = None
        # Start on dashboard instead of invoice
        self.show_page("dashboard")

    # ---------- UI bits ----------
    def _build_topbar(self):
        self.topbar = ctk.CTkFrame(self, corner_radius=12)
        self.topbar.grid(row=0, column=0, columnspan=2, sticky="ew", padx=16, pady=(16, 8))

        title = ctk.CTkLabel(self.topbar, text="InvoiceMint", font=("Segoe UI", 20, "bold"))
        title.pack(side="left", padx=14, pady=10)

        # Open Saved dropdown (modern touch)
        self.open_btn = ctk.CTkSegmentedButton(self.topbar, values=["Open Saved"])
        self.open_btn.set("Open Saved")
        self.open_btn.configure(command=self._open_saved_popup)
        self.open_btn.pack(side="right", padx=(0, 8), pady=10)

        theme_btn = ctk.CTkButton(self.topbar, text="Toggle Theme", width=120, command=self.toggle_theme)
        theme_btn.pack(side="right", padx=8, pady=10)

        # New Quote / New Invoice now pass doc_type to the builder
        new_quote = ctk.CTkButton(
            self.topbar,
            text="New Quote",
            width=110,
            command=lambda: self.show_page("invoice", doc_type="quote"),
        )
        new_quote.pack(side="right", padx=8, pady=10)

        new_invoice = ctk.CTkButton(
            self.topbar,
            text="New Invoice",
            width=110,
            command=lambda: self.show_page("invoice", doc_type="invoice"),
        )
        new_invoice.pack(side="right", padx=8, pady=10)

    def _build_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, corner_radius=16)
        self.sidebar.grid(row=1, column=0, sticky="nsw", padx=(16, 8), pady=(0, 16))
        for label, key in [
            ("Dashboard", "dashboard"),   # <-- now actually points to dashboard
            ("Clients", "clients"),
            ("Templates", "templates"),
            ("Drafts / History", "history"),
            ("Settings", "settings"),
        ]:
            btn = ctk.CTkButton(
                self.sidebar,
                text=label,
                corner_radius=10,
                anchor="w",
                fg_color=("white", "#151a21"),
                text_color=("black", "white"),
                hover_color=("#e8eef7", "#222a34"),
                width=160,
                command=lambda k=key: self.show_page(k),
            )
            btn.pack(fill="x", padx=10, pady=6)

    # ---------- Behavior ----------
    def toggle_theme(self):
        mode = ctk.get_appearance_mode()
        new_mode = "Dark" if mode == "Light" else "Light"
        ctk.set_appearance_mode(new_mode)
        self.settings["theme"] = "dark" if new_mode == "Dark" else "light"
        save_settings(self.settings)

    def _open_saved_popup(self):
        drafts = list_drafts()
        if not drafts:
            # small toast
            toast = ctk.CTkToplevel(self)
            toast.title("No drafts")
            ctk.CTkLabel(
                toast,
                text="No saved drafts yet. Use “Save Draft” from Invoice page.",
            ).pack(padx=16, pady=16)
            toast.geometry("+%d+%d" % (self.winfo_rootx() + 120, self.winfo_rooty() + 80))
            toast.after(2000, toast.destroy)
            return

        # lightweight chooser
        win = ctk.CTkToplevel(self)
        win.title("Open Draft")
        win.geometry("420x320")
        frame = ctk.CTkScrollableFrame(win)
        frame.pack(fill="both", expand=True, padx=12, pady=12)
        for d in drafts:
            row = ctk.CTkFrame(frame, corner_radius=8)
            row.pack(fill="x", padx=4, pady=6)
            ctk.CTkLabel(row, text=d["name"]).pack(side="left", padx=10, pady=10)
            ctk.CTkButton(
                row,
                text="Open",
                width=80,
                command=lambda p=d["path"]: self._open_draft_and_switch(p),
            ).pack(side="right", padx=8, pady=8)

    def _open_draft_and_switch(self, path):
        """
        Open a saved draft in the invoice/quote builder.
        We first load the draft to inspect its doc_type, then open the correct mode.
        """
        state = load_draft(path) or {}
        doc_type = state.get("doc_type", "invoice")

        self.show_page("invoice", doc_type=doc_type)

        # Prefer set_state if available; fallback to load_from_path
        if hasattr(self.current_page, "set_state"):
            self.current_page.set_state(state)
        elif hasattr(self.current_page, "load_from_path"):
            self.current_page.load_from_path(path)

    def _open_state_in_invoice(self, state_dict: dict):
        """Callback for DraftsHistory: show invoice page and load given state."""
        doc_type = state_dict.get("doc_type", "invoice")
        self.show_page("invoice", doc_type=doc_type)
        if hasattr(self.current_page, "set_state"):
            self.current_page.set_state(state_dict)

    def show_page(self, key: str, doc_type: str | None = None):
        if self.current_page is not None:
            self.current_page.destroy()

        if key == "dashboard":
            # pass app=self so dashboard can navigate/open docs if it wants
            self.current_page = DashboardPage(self.content, app=self)
        elif key == "invoice":
            # Pass doc_type down; default to "invoice"
            dt = doc_type or "invoice"
            self.current_page = InvoiceBuilder(self.content, doc_type=dt)
        elif key == "clients":
            self.current_page = ClientsPage(self.content)
        elif key == "templates":
            self.current_page = TemplatesPage(self.content)
        elif key == "history":
            # Pass a callback so the history page can load into the builder
            self.current_page = DraftsHistory(self.content, on_open_state=self._open_state_in_invoice)
        elif key == "settings":
            self.current_page = SettingsPage(self.content)
        else:
            self.current_page = ctk.CTkFrame(self.content, corner_radius=16)

        self.current_page.grid(row=0, column=0, sticky="nsew")
