import customtkinter as ctk
import tkinter as tk
from datetime import datetime, date
from pathlib import Path
import os
import sys
import subprocess

from invoicemint.services.storage import (
    list_drafts, load_draft, delete_draft, rename_draft, save_draft
)


class DraftsHistory(ctk.CTkFrame):
    def __init__(self, parent, on_open_state=None):
        """
        on_open_state: callback(state_dict) -> None
        Pass InvoiceBuilder.set_state so clicking "Open" loads into the builder.
        """
        super().__init__(parent, corner_radius=12)
        self.on_open_state = on_open_state
        self._build()
        self.refresh()

    # ---------- small helpers ----------
    def _center_and_modal(self, win: tk.Toplevel, w=380, h=160):
        self.update_idletasks()
        try:
            x = self.winfo_rootx() + (self.winfo_width() - w) // 2
            y = self.winfo_rooty() + (self.winfo_height() - h) // 2
        except Exception:
            x = self.winfo_rootx() + 80
            y = self.winfo_rooty() + 80
        win.geometry(f"{w}x{h}+{max(0,x)}+{max(0,y)}")
        win.transient(self.winfo_toplevel())
        win.attributes("-topmost", True)
        win.grab_set()
        win.focus_set()

    def _reveal_in_fs(self, path: str | Path):
        p = str(Path(path).resolve())
        try:
            if sys.platform.startswith("win"):
                os.startfile(Path(p).parent)  # type: ignore
            elif sys.platform == "darwin":
                subprocess.run(["open", "-R", p])
            else:
                subprocess.run(["xdg-open", str(Path(p).parent)])
        except Exception:
            pass

    # ---------- UI ----------
    def _build(self):
        header = ctk.CTkFrame(self, corner_radius=12)
        header.pack(fill="x", padx=12, pady=(12, 6))

        ctk.CTkLabel(
            header,
            text="Drafts / History",
            font=("Segoe UI", 16, "bold"),
        ).pack(side="left", padx=10, pady=10)
        ctk.CTkButton(header, text="Refresh", command=self.refresh).pack(
            side="right", padx=10, pady=10
        )

        # table header
        th = ctk.CTkFrame(self, corner_radius=10)
        th.pack(fill="x", padx=12, pady=(0, 4))
        for i, (text, w) in enumerate([
            ("Name", 220),
            ("Type", 80),
            ("Modified", 160),
            ("Actions", 260),
        ]):
            ctk.CTkLabel(th, text=text).grid(row=0, column=i, padx=8, pady=8, sticky="w")
            th.grid_columnconfigure(i, minsize=w)

        self.table = ctk.CTkScrollableFrame(self, corner_radius=12, height=460)
        self.table.pack(fill="both", expand=True, padx=12, pady=(0, 12))

    def refresh(self):
        for child in self.table.winfo_children():
            child.destroy()

        drafts = sorted(list_drafts(), key=lambda d: d.get("mtime", 0), reverse=True)
        if not drafts:
            ctk.CTkLabel(
                self.table,
                text="No drafts yet.",
                text_color=("#6b7280", "#9ca3af"),
            ).pack(padx=16, pady=16)
            return

        for d in drafts:
            row = ctk.CTkFrame(self.table, corner_radius=8)
            row.pack(fill="x", padx=6, pady=6)

            name = d.get("name", "")
            when = datetime.fromtimestamp(d.get("mtime", 0)).strftime("%Y-%m-%d %H:%M")
            path = d.get("path", "")

            # Load state to detect type + totals (best-effort; ignore errors)
            doc_type = "Invoice"
            try:
                state = load_draft(path) or {}
                doc_type = state.get("doc_type", "invoice").capitalize()
            except Exception:
                state = {}

            # Name
            ctk.CTkLabel(row, text=name, anchor="w").grid(
                row=0, column=0, padx=10, pady=10, sticky="w"
            )

            # Type (Invoice / Quote)
            type_color = ("#6b7280", "#9ca3af")
            if doc_type.lower() == "quote":
                type_color = ("#0f766e", "#34d399")  # a bit more prominent for quotes
            ctk.CTkLabel(
                row,
                text=doc_type,
                text_color=type_color,
            ).grid(row=0, column=1, padx=10, pady=10, sticky="w")

            # Modified timestamp
            ctk.CTkLabel(
                row,
                text=when,
                text_color=("#6b7280", "#9ca3af"),
            ).grid(row=0, column=2, padx=10, pady=10, sticky="w")

            # Actions
            btns = ctk.CTkFrame(row, fg_color="transparent")
            btns.grid(row=0, column=3, padx=8, pady=8, sticky="e")

            # Open
            ctk.CTkButton(
                btns,
                text="Open",
                width=72,
                command=lambda p=path: self._open_draft(p),
            ).pack(side="left", padx=4)

            # For quotes, offer "Convert to Invoice"
            if doc_type.lower() == "quote":
                ctk.CTkButton(
                    btns,
                    text="Convert to Invoice",
                    width=140,
                    command=lambda p=path: self._convert_quote_to_invoice(p),
                ).pack(side="left", padx=4)

            # Rename
            ctk.CTkButton(
                btns,
                text="Rename",
                width=72,
                command=lambda p=path: self._rename(p),
            ).pack(side="left", padx=4)

            # Delete
            ctk.CTkButton(
                btns,
                text="Delete",
                width=72,
                fg_color="#b91c1c",
                command=lambda p=path: self._delete(p),
            ).pack(side="left", padx=4)

            # Reveal in file system
            ctk.CTkButton(
                btns,
                text="Reveal",
                width=72,
                command=lambda p=path: self._reveal_in_fs(p),
            ).pack(side="left", padx=4)

            for i, w in enumerate([220, 80, 160, 260]):
                row.grid_columnconfigure(i, minsize=w)
            row.grid_columnconfigure(0, weight=1)

    # ---------- actions ----------
    def _open_draft(self, path):
        try:
            state = load_draft(path)
            if state and callable(self.on_open_state):
                self.on_open_state(state)
        except Exception:
            pass

    def _convert_quote_to_invoice(self, path: str):
        """
        Load a quote draft, convert it to an invoice, save as a new draft,
        and open it in the invoice builder via on_open_state.
        """
        try:
            state = load_draft(path) or {}
        except Exception:
            return

        if not state:
            return

        if state.get("doc_type") != "quote":
            # nothing to convert if it's already an invoice
            return

        # Create a new invoice-based state from the quote
        new_state = dict(state)
        new_state["doc_type"] = "invoice"

        # Update date fields to "today" for the new invoice
        meta = dict(new_state.get("meta") or {})
        today_str = date.today().isoformat()
        meta["date"] = today_str
        new_state["meta"] = meta
        new_state["date"] = today_str

        # Optionally adjust status for the new invoice
        # (keep whatever was on the quote for now)
        # new_state["status"] = meta.get("status", "")

        # Save as a new draft with an auto name (timestamped)
        save_draft(new_state)

        # Open it in the invoice builder
        if callable(self.on_open_state):
            self.on_open_state(new_state)

        # Small toast so user sees something happened
        toast = ctk.CTkToplevel(self)
        toast.title("Converted")
        ctk.CTkLabel(
            toast,
            text="Quote converted to a new invoice draft.",
        ).pack(padx=16, pady=16)
        self._center_and_modal(toast, 320, 140)
        toast.after(1200, toast.destroy)

        # Refresh the list so the new invoice appears
        self.refresh()

    def _rename(self, path):
        dlg = ctk.CTkInputDialog(title="Rename Draft", text="New name:")
        new_name = dlg.get_input()
        if not new_name:
            return
        newp = rename_draft(path, new_name)
        toast = ctk.CTkToplevel(self)
        toast.title("Rename")
        msg = f"Renamed to:\n{Path(newp).name}" if newp else "Rename failed."
        ctk.CTkLabel(toast, text=msg).pack(padx=16, pady=16)
        self._center_and_modal(toast, 320, 140)
        toast.after(1200, toast.destroy)
        self.refresh()

    def _delete(self, path):
        confirm = ctk.CTkInputDialog(
            title="Delete Draft",
            text="Type DELETE to confirm:",
        )
        if (confirm.get_input() or "").strip().upper() != "DELETE":
            return
        ok = delete_draft(path)
        toast = ctk.CTkToplevel(self)
        toast.title("Delete")
        ctk.CTkLabel(
            toast,
            text="Deleted." if ok else "Delete failed.",
        ).pack(padx=16, pady=16)
        self._center_and_modal(toast, 260, 120)
        toast.after(1000, toast.destroy)
        self.refresh()
