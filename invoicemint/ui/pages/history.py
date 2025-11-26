import customtkinter as ctk
import tkinter as tk
from datetime import datetime
from pathlib import Path
import os
import sys
import subprocess

from invoicemint.services.storage import (
    list_drafts, load_draft, delete_draft, rename_draft
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
        header.pack(fill="x", padx=12, pady=(12,6))

        ctk.CTkLabel(header, text="Drafts / History", font=("Segoe UI", 16, "bold")).pack(side="left", padx=10, pady=10)
        ctk.CTkButton(header, text="Refresh", command=self.refresh).pack(side="right", padx=10, pady=10)

        # table header
        th = ctk.CTkFrame(self, corner_radius=10)
        th.pack(fill="x", padx=12, pady=(0,4))
        for i, (text, w) in enumerate([
            ("Name", 260), ("Modified", 160), ("Actions", 260)
        ]):
            ctk.CTkLabel(th, text=text).grid(row=0, column=i, padx=8, pady=8, sticky="w")
            th.grid_columnconfigure(i, minsize=w)

        self.table = ctk.CTkScrollableFrame(self, corner_radius=12, height=460)
        self.table.pack(fill="both", expand=True, padx=12, pady=(0,12))

    def refresh(self):
        for child in self.table.winfo_children():
            child.destroy()

        drafts = sorted(list_drafts(), key=lambda d: d.get("mtime", 0), reverse=True)
        if not drafts:
            ctk.CTkLabel(self.table, text="No drafts yet.", text_color=("#6b7280", "#9ca3af")).pack(padx=16, pady=16)
            return

        for d in drafts:
            row = ctk.CTkFrame(self.table, corner_radius=8)
            row.pack(fill="x", padx=6, pady=6)

            name = d.get("name", "")
            when = datetime.fromtimestamp(d.get("mtime", 0)).strftime("%Y-%m-%d %H:%M")
            path = d.get("path", "")

            ctk.CTkLabel(row, text=name, anchor="w").grid(row=0, column=0, padx=10, pady=10, sticky="w")
            ctk.CTkLabel(row, text=when, text_color=("#6b7280", "#9ca3af")).grid(row=0, column=1, padx=10, pady=10, sticky="w")

            btns = ctk.CTkFrame(row, fg_color="transparent")
            btns.grid(row=0, column=2, padx=8, pady=8, sticky="e")

            ctk.CTkButton(btns, text="Open", width=72,
                          command=lambda p=path: self._open_draft(p)).pack(side="left", padx=4)
            ctk.CTkButton(btns, text="Rename", width=72,
                          command=lambda p=path: self._rename(p)).pack(side="left", padx=4)
            ctk.CTkButton(btns, text="Delete", width=72, fg_color="#b91c1c",
                          command=lambda p=path: self._delete(p)).pack(side="left", padx=4)
            ctk.CTkButton(btns, text="Reveal", width=72,
                          command=lambda p=path: self._reveal_in_fs(p)).pack(side="left", padx=4)

            for i, w in enumerate([260, 160, 260]):
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

    def _rename(self, path):
        dlg = ctk.CTkInputDialog(title="Rename Draft", text="New name:")
        new_name = dlg.get_input()
        if not new_name:
            return
        newp = rename_draft(path, new_name)
        toast = ctk.CTkToplevel(self); toast.title("Rename")
        msg = f"Renamed to:\n{Path(newp).name}" if newp else "Rename failed."
        ctk.CTkLabel(toast, text=msg).pack(padx=16, pady=16)
        self._center_and_modal(toast, 320, 140)
        toast.after(1200, toast.destroy)
        self.refresh()

    def _delete(self, path):
        confirm = ctk.CTkInputDialog(title="Delete Draft",
                                     text="Type DELETE to confirm:")
        if (confirm.get_input() or "").strip().upper() != "DELETE":
            return
        ok = delete_draft(path)
        toast = ctk.CTkToplevel(self); toast.title("Delete")
        ctk.CTkLabel(toast, text="Deleted." if ok else "Delete failed.").pack(padx=16, pady=16)
        self._center_and_modal(toast, 260, 120)
        toast.after(1000, toast.destroy)
        self.refresh()
