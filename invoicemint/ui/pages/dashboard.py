import customtkinter as ctk

from invoicemint.services.storage import get_recent_documents, DRAFTS_DIR


class DashboardPage(ctk.CTkFrame):
    """
    Dashboard landing page.

    - Shows a title and subtitle
    - Quick actions (New Invoice, View History, Manage Clients)
    - List of recent documents (invoices/quotes)
    """

    def __init__(self, master, app, **kwargs):
        """
        :param master: parent widget (e.g. content frame in MainApp)
        :param app: reference to the MainApp instance so we can call app.show_page(...)
        """
        super().__init__(master, **kwargs)
        self.app = app

        self._build_ui()
        self.refresh()

    # --------------------------------------------------------------------- UI

    def _build_ui(self):
        # Main grid
        self.grid_rowconfigure(3, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Header
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))
        header_frame.grid_columnconfigure(0, weight=1)

        title_label = ctk.CTkLabel(
            header_frame,
            text="InvoiceMint Dashboard",
            font=ctk.CTkFont(size=24, weight="bold"),
        )
        title_label.grid(row=0, column=0, sticky="w")

        subtitle_label = ctk.CTkLabel(
            header_frame,
            text="Quick overview of your recent invoices and quotes.",
            font=ctk.CTkFont(size=13),
        )
        subtitle_label.grid(row=1, column=0, sticky="w", pady=(4, 0))

        # Quick actions row
        actions_frame = ctk.CTkFrame(self)
        actions_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=(10, 10))
        for i in range(3):
            actions_frame.grid_columnconfigure(i, weight=1)

        new_invoice_btn = ctk.CTkButton(
            actions_frame,
            text="➕ New Invoice",
            command=lambda: self._go_to("invoice"),
        )
        new_invoice_btn.grid(row=0, column=0, padx=8, pady=10, sticky="ew")

        history_btn = ctk.CTkButton(
            actions_frame,
            text="📄 View History",
            command=lambda: self._go_to("history"),
        )
        history_btn.grid(row=0, column=1, padx=8, pady=10, sticky="ew")

        clients_btn = ctk.CTkButton(
            actions_frame,
            text="👥 Manage Clients",
            command=lambda: self._go_to("clients"),
        )
        clients_btn.grid(row=0, column=2, padx=8, pady=10, sticky="ew")

        # Stats + recent docs container
        lower_frame = ctk.CTkFrame(self)
        lower_frame.grid(row=2, column=0, sticky="nsew", padx=20, pady=(10, 20))
        lower_frame.grid_rowconfigure(1, weight=1)
        lower_frame.grid_columnconfigure(0, weight=1)
        lower_frame.grid_columnconfigure(1, weight=2)

        # Simple stats (you can expand this later)
        stats_frame = ctk.CTkFrame(lower_frame)
        stats_frame.grid(row=0, column=0, rowspan=2, sticky="nsew", padx=(10, 5), pady=10)
        stats_frame.grid_columnconfigure(0, weight=1)

        self.total_docs_label = ctk.CTkLabel(
            stats_frame,
            text="Total documents: 0",
            font=ctk.CTkFont(size=14, weight="bold"),
        )
        self.total_docs_label.grid(row=0, column=0, sticky="w", padx=10, pady=(10, 4))

        self.invoice_count_label = ctk.CTkLabel(
            stats_frame,
            text="Invoices: 0",
            font=ctk.CTkFont(size=13),
        )
        self.invoice_count_label.grid(row=1, column=0, sticky="w", padx=10, pady=2)

        self.quote_count_label = ctk.CTkLabel(
            stats_frame,
            text="Quotes: 0",
            font=ctk.CTkFont(size=13),
        )
        self.quote_count_label.grid(row=2, column=0, sticky="w", padx=10, pady=2)

        # Recent docs list
        recent_frame = ctk.CTkFrame(lower_frame)
        recent_frame.grid(row=0, column=1, rowspan=2, sticky="nsew", padx=(5, 10), pady=10)
        recent_frame.grid_rowconfigure(1, weight=1)
        recent_frame.grid_columnconfigure(0, weight=1)

        header = ctk.CTkLabel(
            recent_frame,
            text="Recent documents",
            font=ctk.CTkFont(size=14, weight="bold"),
        )
        header.grid(row=0, column=0, sticky="w", padx=10, pady=(10, 4))

        self.recent_list = ctk.CTkScrollableFrame(recent_frame)
        self.recent_list.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        self.recent_list.grid_columnconfigure(0, weight=1)

        self._empty_label = ctk.CTkLabel(
            self.recent_list,
            text="No documents yet. Create your first invoice to see it here.",
            font=ctk.CTkFont(size=12, slant="italic"),
        )
        self._empty_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")

    # ----------------------------------------------------------------- actions

    def _go_to(self, page_name: str):
        """
        Navigate to another page in the main app.
        Assumes MainApp has a .show_page(name: str) method.
        """
        if hasattr(self.app, "show_page"):
            self.app.show_page(page_name)

    # ----------------------------------------------------------------- refresh

    def refresh(self):
        """
        Reload stats and recent documents.
        Call this when the dashboard is shown to keep it up to date.
        """
        docs = get_recent_documents(limit=10)

        # Update stats
        total = len(docs)
        invoices = sum(1 for d in docs if d.get("doc_type") == "invoice")
        quotes = sum(1 for d in docs if d.get("doc_type") == "quote")

        self.total_docs_label.configure(text=f"Total documents: {total}")
        self.invoice_count_label.configure(text=f"Invoices: {invoices}")
        self.quote_count_label.configure(text=f"Quotes: {quotes}")

        # Clear existing rows in recent_list
        for widget in self.recent_list.winfo_children():
            widget.destroy()

        if not docs:
            self._empty_label = ctk.CTkLabel(
                self.recent_list,
                text="No documents yet. Create your first invoice to see it here.",
                font=ctk.CTkFont(size=12, slant="italic"),
            )
            self._empty_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")
            return

        # Re-build rows
        for row_index, doc in enumerate(docs):
            row = ctk.CTkFrame(self.recent_list)
            row.grid(row=row_index, column=0, sticky="ew", padx=0, pady=4)
            row.grid_columnconfigure(0, weight=1)
            row.grid_columnconfigure(1, weight=0)

            title = f"{doc.get('client_name', 'Unknown client')}"

            doc_type = doc.get("doc_type", "invoice").capitalize()
            date_str = doc.get("date") or ""
            total = doc.get("total")

            # Left text: client + meta
            main_label = ctk.CTkLabel(
                row,
                justify="left",
                text=f"{title}\n{doc_type} • {date_str}",
            )
            main_label.grid(row=0, column=0, sticky="w", padx=10, pady=6)

            # Right side: amount + open button
            right_frame = ctk.CTkFrame(row, fg_color="transparent")
            right_frame.grid(row=0, column=1, sticky="e", padx=10, pady=6)
            right_frame.grid_columnconfigure(0, weight=0)
            right_frame.grid_columnconfigure(1, weight=0)

            if total is not None:
                amount_label = ctk.CTkLabel(
                    right_frame,
                    text=f"${total:,.2f}",
                    font=ctk.CTkFont(size=13, weight="bold"),
                )
                amount_label.grid(row=0, column=0, sticky="e", padx=(0, 8))

            # Use filename so we can build the exact path in _open_document
            open_btn = ctk.CTkButton(
                right_frame,
                text="Open",
                width=70,
                command=lambda filename=doc["filename"]: self._open_document(filename),
            )
            open_btn.grid(row=0, column=1, sticky="e")

    def _open_document(self, filename: str):
        """
        Open a specific document in the invoice page using MainApp's existing
        _open_draft_and_switch helper.
        """
        # Build full path from DRAFTS_DIR + filename
        path = DRAFTS_DIR / filename

        # Prefer using the existing helper on MainApp
        if hasattr(self.app, "_open_draft_and_switch"):
            self.app._open_draft_and_switch(str(path))
        else:
            # Fallback: just go to history if for some reason that helper is missing
            self._go_to("history")
