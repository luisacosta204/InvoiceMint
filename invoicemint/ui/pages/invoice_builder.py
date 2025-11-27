# invoicemint/ui/pages/invoice_builder.py
import customtkinter as ctk
from customtkinter import CTkInputDialog
import tkinter as tk
from tkinter import filedialog
from datetime import datetime, timedelta
import os
import sys
import tempfile
import subprocess

from invoicemint.services.storage import (
    save_draft, load_draft, list_drafts, load_settings, save_settings, load_clients,
)
from invoicemint.services.pdf import generate_invoice_pdf

# column widths (header == rows)
COL_SERVICE = 160
COL_DESC    = 320
COL_QTY     = 60
COL_UNIT    = 100
COL_TAX     = 70
COL_TOTAL   = 100
COL_REMOVE  = 50

TERMS_OPTIONS = ["Due on receipt", "Net 7", "Net 14", "Net 30"]


def _today_str():
    return datetime.now().strftime("%Y-%m-%d")


def _add_days(date_str: str, days: int) -> str:
    try:
        d = datetime.strptime(date_str, "%Y-%m-%d")
    except Exception:
        d = datetime.now()
    return (d + timedelta(days=days)).strftime("%Y-%m-%d")


class InvoiceBuilder(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, corner_radius=16)
        self.rows = []
        self.clients = []
        self.client_names = []
        self.selected_client = None
        self.client_vars = {}  # editable per-invoice fields

        # invoice meta
        self.inv_no_var = tk.StringVar()
        self.inv_date_var = tk.StringVar(value=_today_str())
        self.due_date_var = tk.StringVar(value=_add_days(_today_str(), 14))
        self.terms_var = tk.StringVar(value="Net 14")
        self.status_var = tk.StringVar(value="No watermark")  # default status

        self._init_invoice_number()
        self._build()

    # -------- invoice number bootstrap ----------
    def _init_invoice_number(self):
        settings = load_settings() or {}
        seq = int(settings.get("invoice_seq", 1001))
        self.inv_no_var.set(str(seq))

    def _next_invoice_number(self):
        try:
            return str(int(self.inv_no_var.get().strip() or "0") + 1)
        except Exception:
            return str(int((load_settings() or {}).get("invoice_seq", 1001)) + 1)

    # ---------- UI ----------
    def _build(self):
        # rows area (items) is the stretchy part
        self.grid_rowconfigure(3, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Top bar: client selector + invoice meta
        top = ctk.CTkFrame(self, corner_radius=12)
        top.grid(row=0, column=0, sticky="ew", padx=12, pady=(12, 6))

        # Left: client selector
        ctk.CTkLabel(top, text="Client").grid(row=0, column=0, padx=8, pady=10, sticky="w")
        self.client_var = tk.StringVar(value="(No client selected)")
        self.client_menu = ctk.CTkOptionMenu(
            top,
            values=["(No client selected)"],
            variable=self.client_var,
            width=320,
            command=self._on_pick_client,
        )
        self.client_menu.grid(row=0, column=1, padx=8, pady=10, sticky="w")
        ctk.CTkButton(top, text="Refresh", width=100, command=self._reload_clients).grid(
            row=0, column=2, padx=8, pady=10
        )

        # Right: invoice meta (number + dates + terms)
        meta = ctk.CTkFrame(top, corner_radius=8)
        meta.grid(row=0, column=3, padx=8, pady=10, sticky="e")
        for i in range(6):
            meta.grid_columnconfigure(i, minsize=10)

        ctk.CTkLabel(meta, text="Invoice #").grid(row=0, column=0, padx=(10, 6), pady=6, sticky="e")
        ctk.CTkEntry(meta, textvariable=self.inv_no_var, width=90).grid(
            row=0, column=1, padx=(0, 8), pady=6
        )
        ctk.CTkButton(meta, text="↻", width=34, command=self._regen_invoice_no).grid(
            row=0, column=2, padx=(0, 10), pady=6
        )

        ctk.CTkLabel(meta, text="Date").grid(row=0, column=3, padx=(6, 6), pady=6, sticky="e")
        ctk.CTkEntry(
            meta, textvariable=self.inv_date_var, width=110, placeholder_text="YYYY-MM-DD"
        ).grid(row=0, column=4, padx=(0, 10), pady=6)

        ctk.CTkLabel(meta, text="Terms").grid(row=0, column=5, padx=(6, 6), pady=6, sticky="e")
        self.terms_menu = ctk.CTkOptionMenu(
            meta,
            values=TERMS_OPTIONS,
            variable=self.terms_var,
            width=120,
            command=self._on_terms_change,
        )
        self.terms_menu.grid(row=0, column=6, padx=(0, 10), pady=6)

        ctk.CTkLabel(meta, text="Due").grid(row=0, column=7, padx=(6, 6), pady=6, sticky="e")
        ctk.CTkEntry(
            meta, textvariable=self.due_date_var, width=110, placeholder_text="YYYY-MM-DD"
        ).grid(row=0, column=8, padx=(0, 10), pady=6)

        # Status row under invoice number
        ctk.CTkLabel(meta, text="Status").grid(
            row=1, column=0, padx=(10, 6), pady=6, sticky="e"
        )
        self.status_menu = ctk.CTkOptionMenu(
            meta,
            values=["UNPAID", "PAID", "OVERDUE", "No watermark"],
            variable=self.status_var,
            width=140,
        )
        self.status_menu.grid(row=1, column=1, padx=(0, 8), pady=6, sticky="w")

        top.grid_columnconfigure(4, weight=1)  # spacer so meta stays right

        # Editable client card (for this invoice only)
        self.client_card = ctk.CTkFrame(self, corner_radius=12)
        self.client_card.grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 8))
        self._build_client_card()

        # Header
        header = ctk.CTkFrame(self, corner_radius=12)
        header.grid(row=2, column=0, sticky="ew", padx=12, pady=(4, 4))
        lbls = ["Service / Item", "Description", "Qty", "Unit Price", "Tax %", "Total", ""]
        mins = [COL_SERVICE, COL_DESC, COL_QTY, COL_UNIT, COL_TAX, COL_TOTAL, COL_REMOVE]
        for i, (t, w) in enumerate(zip(lbls, mins)):
            ctk.CTkLabel(header, text=t).grid(row=0, column=i, padx=6, pady=8, sticky="w")
            header.grid_columnconfigure(i, minsize=w)

        # Rows area
        self.scroll = ctk.CTkScrollableFrame(self, corner_radius=12, height=420)
        self.scroll.grid(row=3, column=0, sticky="nsew", padx=12)

        # Footer actions
        footer = ctk.CTkFrame(self, corner_radius=12)
        footer.grid(row=4, column=0, sticky="ew", padx=12, pady=(8, 12))
        ctk.CTkButton(footer, text="+ Add Item", command=self.add_row).pack(
            side="left", padx=6, pady=8
        )
        ctk.CTkButton(
            footer, text="Save Draft", command=self.on_save, fg_color="#2563eb"
        ).pack(side="left", padx=6, pady=8)
        ctk.CTkButton(footer, text="Load Draft", command=self.on_load).pack(
            side="left", padx=6, pady=8
        )
        ctk.CTkButton(footer, text="Preview PDF", command=self.on_preview_pdf).pack(
            side="right", padx=6, pady=8
        )
        ctk.CTkButton(footer, text="Export PDF", command=self.on_export_pdf).pack(
            side="right", padx=6, pady=8
        )

        # Notes area (per-invoice)
        notes = ctk.CTkFrame(self, corner_radius=12)
        notes.grid(row=5, column=0, sticky="ew", padx=12, pady=(0, 8))

        ctk.CTkLabel(notes, text="Notes").pack(anchor="w", padx=10, pady=(8, 0))

        self.notes_text = ctk.CTkTextbox(notes, height=70)
        self.notes_text.pack(fill="x", padx=10, pady=(4, 8))

        # Default text from settings (fallback to a sane default)
        s = load_settings() or {}
        default_notes = s.get(
            "default_notes",
            "Thank you for your business!\nPayment is due in 14 days.",
        )
        self.notes_text.insert("1.0", default_notes)

        # Totals
        totals = ctk.CTkFrame(self, corner_radius=12)
        totals.grid(row=6, column=0, sticky="e", padx=12, pady=(0, 12))
        self.subtotal_var = tk.StringVar(value="0.00")
        self.tax_var = tk.StringVar(value="0.00")
        self.total_var = tk.StringVar(value="0.00")

        def trow(label, var=None, bold=False):
            font = ("Segoe UI", 12, "bold") if bold else None
            ctk.CTkLabel(totals, text=label, font=font).pack(
                side="left", padx=(10, 6), pady=10
            )
            if var is not None:
                ctk.CTkLabel(totals, textvariable=var, font=font).pack(
                    side="left", padx=(0, 10), pady=10
                )

        trow("Subtotal:", self.subtotal_var)
        trow("Total Tax:", self.tax_var)
        trow("Grand Total:", self.total_var, bold=True)

        # bootstrap
        self._reload_clients()
        self.add_row()

    def _build_client_card(self):
        labels = [
            ("Business / Name", "business_or_name"),
            ("Address", "address"),
            ("Email", "email"),
            ("Phone", "phone"),
        ]
        self.client_vars = {key: tk.StringVar() for _, key in labels}
        for i, (label, key) in enumerate(labels):
            ctk.CTkLabel(self.client_card, text=label).grid(
                row=i // 2, column=(i % 2) * 2, padx=10, pady=8, sticky="e"
            )
            ent = ctk.CTkEntry(
                self.client_card,
                textvariable=self.client_vars[key],
                width=360,
                placeholder_text=f"Enter {label.lower()}",
            )
            ent.grid(row=i // 2, column=(i % 2) * 2 + 1, padx=10, pady=8, sticky="w")
        self._apply_client_to_card({})

    # ---------- helpers ----------
    def _apply_client_to_card(self, client):
        display_name = client.get("business") or client.get("name") or ""
        self.client_vars["business_or_name"].set(display_name)
        self.client_vars["address"].set(client.get("address", ""))
        self.client_vars["email"].set(client.get("email", ""))
        self.client_vars["phone"].set(client.get("phone", ""))

    def _open_file(self, path: str):
        """Open a file with the default system viewer."""
        try:
            if sys.platform.startswith("win"):
                os.startfile(path)  # type: ignore[attr-defined]
            elif sys.platform == "darwin":
                subprocess.Popen(["open", path])
            else:
                subprocess.Popen(["xdg-open", path])
        except Exception as exc:
            print(f"Could not open file {path!r}: {exc}")

    def _reload_clients(self, *_):
        self.clients = load_clients() or []

        def display(c):
            return c.get("business") or c.get("name") or c.get("email", "Unnamed")

        self.client_names = ["(No client selected)"] + [display(c) for c in self.clients]
        self.client_menu.configure(values=self.client_names)
        if self.client_var.get() not in self.client_names:
            self.client_var.set("(No client selected)")
            self.selected_client = None
            self._apply_client_to_card({})

    def _on_pick_client(self, name):
        if name == "(No client selected)":
            self.selected_client = None
            self._apply_client_to_card({})
            return
        idx = self.client_names.index(name) - 1
        self.selected_client = self.clients[idx] if 0 <= idx < len(self.clients) else None
        self._apply_client_to_card(self.selected_client or {})

    def _on_terms_change(self, selected):
        days = 0
        if selected == "Net 7":
            days = 7
        elif selected == "Net 14":
            days = 14
        elif selected == "Net 30":
            days = 30
        self.due_date_var.set(
            _add_days(self.inv_date_var.get() or _today_str(), days)
        )

    def _regen_invoice_no(self):
        self.inv_no_var.set(self._next_invoice_number())

    # ---------- rows ----------
    def add_row(self, preset=None):
        idx = len(self.rows)
        row = ctk.CTkFrame(self.scroll, corner_radius=10)
        row.grid(row=idx, column=0, sticky="ew", padx=4, pady=6)
        self.scroll.grid_columnconfigure(0, weight=1)

        e_service = ctk.CTkEntry(row, placeholder_text="Service / Item", width=COL_SERVICE)
        t_desc = ctk.CTkTextbox(row, width=COL_DESC, height=60)
        e_qty = ctk.CTkEntry(row, width=COL_QTY)
        e_price = ctk.CTkEntry(row, width=COL_UNIT)
        e_tax = ctk.CTkEntry(row, width=COL_TAX)
        l_total = ctk.CTkLabel(row, text="0.00", width=COL_TOTAL, anchor="e")
        b_remove = ctk.CTkButton(
            row, text="✕", width=COL_REMOVE, fg_color=("#eeeeee", "#1f2937")
        )

        e_service.grid(row=0, column=0, padx=6, pady=8, sticky="w")
        t_desc.grid(row=0, column=1, padx=6, pady=8, sticky="we")
        e_qty.grid(row=0, column=2, padx=6, pady=8)
        e_price.grid(row=0, column=3, padx=6, pady=8)
        e_tax.grid(row=0, column=4, padx=6, pady=8)
        l_total.grid(row=0, column=5, padx=6, pady=8)
        b_remove.grid(row=0, column=6, padx=6, pady=8)

        for i, w in enumerate(
            [COL_SERVICE, COL_DESC, COL_QTY, COL_UNIT, COL_TAX, COL_TOTAL, COL_REMOVE]
        ):
            row.grid_columnconfigure(i, minsize=w)
        row.grid_columnconfigure(1, weight=1)

        def remove():
            self.rows.remove(tup)
            row.destroy()
            self.recompute()

        b_remove.configure(command=remove)
        for e in (e_qty, e_price, e_tax):
            e.bind("<KeyRelease>", lambda _ev: self.recompute())

        tup = (row, e_service, t_desc, e_qty, e_price, e_tax, l_total)
        self.rows.append(tup)

        if preset:
            e_service.insert(0, preset.get("service", ""))
            t_desc.delete("1.0", "end")
            t_desc.insert("1.0", preset.get("description", ""))
            e_qty.insert(0, str(preset.get("qty", 0)))
            e_price.insert(0, str(preset.get("unit_price", 0)))
            e_tax.insert(0, str(preset.get("tax_pct", 0)))
        self.recompute()

    def recompute(self):
        subtotal = 0.0
        tax_total = 0.0
        for _, _svc, _desc, qty, price, tax, l_total in self.rows:
            try:
                q = float(qty.get() or 0)
                p = float(price.get() or 0)
                t = float(tax.get() or 0)
            except ValueError:
                q = p = t = 0.0
            line = q * p
            line_tax = line * (t / 100.0)
            l_total.configure(text=f"{(line + line_tax):.2f}")
            subtotal += line
            tax_total += line_tax
        self.subtotal_var.set(f"{subtotal:.2f}")
        self.tax_var.set(f"{tax_total:.2f}")
        self.total_var.set(f"{(subtotal + tax_total):.2f}")

    # ---------- state / drafts ----------
    def _current_client_for_state(self):
        base = dict(self.selected_client or {})
        edited_name = self.client_vars["business_or_name"].get().strip()
        if base.get("business") or not base.get("name"):
            base["business"] = edited_name
        else:
            base["name"] = edited_name
        base["address"] = self.client_vars["address"].get().strip()
        base["email"] = self.client_vars["email"].get().strip()
        base["phone"] = self.client_vars["phone"].get().strip()
        return base

    def get_state(self) -> dict:
        items = []
        for _, e_service, t_desc, qty, price, tax, _ in self.rows:
            items.append(
                {
                    "service": e_service.get(),
                    "description": t_desc.get("1.0", "end").rstrip("\n"),
                    "qty": float(qty.get() or 0),
                    "unit_price": float(price.get() or 0),
                    "tax_pct": float(tax.get() or 0),
                }
            )

        # Map "No watermark" UI choice to an empty status so PDFs show no status
        raw_status = (self.status_var.get() or "").strip()
        if raw_status.lower() == "no watermark":
            status_value = ""
        else:
            status_value = raw_status

        return {
            "kind": "invoice",
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "client": self._current_client_for_state(),
            "meta": {
                "number": self.inv_no_var.get().strip(),
                "date": self.inv_date_var.get().strip(),
                "due_date": self.due_date_var.get().strip(),
                "terms": self.terms_var.get().strip(),
                "status": status_value,
            },
            "items": items,
            "totals": {
                "subtotal": float(self.subtotal_var.get()),
                "tax": float(self.tax_var.get()),
                "grand_total": float(self.total_var.get()),
            },
            "notes": self.notes_text.get("1.0", "end").strip(),
        }

    def set_state(self, state: dict):
        # meta
        meta = state.get("meta") or {}
        if "number" in meta:
            self.inv_no_var.set(str(meta["number"]))
        if "date" in meta:
            self.inv_date_var.set(meta["date"])
        if "due_date" in meta:
            self.due_date_var.set(meta["due_date"])
        if "terms" in meta and meta["terms"] in TERMS_OPTIONS:
            self.terms_var.set(meta["terms"])

        # status restore
        stored_status = (meta.get("status") or "").strip()
        if not stored_status:
            # if empty in state, map back to "No watermark"
            self.status_var.set("No watermark")
        else:
            # if it's one of our known options, use it; otherwise just display as-is
            if stored_status in ["UNPAID", "PAID", "OVERDUE"]:
                self.status_var.set(stored_status)
            else:
                self.status_var.set(stored_status)

        # client
        cli = state.get("client") or {}
        self._apply_client_to_card(cli)
        display = cli.get("business") or cli.get("name") or cli.get("email", "")
        if display and display in self.client_names:
            self.client_var.set(display)
        else:
            self.client_var.set("(No client selected)")

        # rows
        for tup in list(self.rows):
            tup[0].destroy()
        self.rows.clear()
        for it in state.get("items", []):
            self.add_row(preset=it)
        if not self.rows:
            self.add_row()
        self.recompute()

        # notes
        if hasattr(self, "notes_text"):
            self.notes_text.delete("1.0", "end")
            if "notes" in state:
                self.notes_text.insert("1.0", state.get("notes", ""))
            else:
                s = load_settings() or {}
                default_notes = s.get(
                    "default_notes",
                    "Thank you for your business!\nPayment is due in 14 days.",
                )
                self.notes_text.insert("1.0", default_notes)

    def on_save(self):
        # ask for a friendly name (default to invoice number)
        default_name = self.inv_no_var.get().strip() or datetime.now().strftime(
            "invoice-%Y%m%d-%H%M%S"
        )
        dialog = CTkInputDialog(
            title="Save Draft", text="Draft name (or leave blank for auto):"
        )
        dialog.entry.insert(0, default_name)
        name = dialog.get_input()
        if name is None:
            return  # user cancelled

        path = save_draft(self.get_state(), name.strip() or None)

        toast = ctk.CTkToplevel(self)
        toast.title("Saved")
        ctk.CTkLabel(toast, text=f"Saved draft:\n{path.name}").pack(
            padx=16, pady=16
        )
        toast.geometry(
            "+%d+%d" % (self.winfo_rootx() + 120, self.winfo_rooty() + 80)
        )
        toast.after(1600, toast.destroy)

    def on_load(self):
        drafts = list_drafts()
        if not drafts:
            toast = ctk.CTkToplevel(self)
            toast.title("No drafts")
            ctk.CTkLabel(toast, text="No saved drafts found.").pack(
                padx=16, pady=16
            )
            toast.geometry(
                "+%d+%d" % (self.winfo_rootx() + 120, self.winfo_rooty() + 80)
            )
            toast.after(1600, toast.destroy)
            return

        win = ctk.CTkToplevel(self)
        win.title("Open Draft")
        win.geometry("420x320")

        # keep this window on top of the main one
        win.transient(self.winfo_toplevel())
        win.grab_set()

        frame = ctk.CTkScrollableFrame(win)
        frame.pack(fill="both", expand=True, padx=12, pady=12)

        for d in drafts:
            row = ctk.CTkFrame(frame, corner_radius=8)
            row.pack(fill="x", padx=4, pady=6)
            ctk.CTkLabel(row, text=d["name"]).pack(
                side="left", padx=10, pady=10
            )
            ctk.CTkButton(
                row,
                text="Open",
                width=80,
                command=lambda p=d["path"]: (self.load_from_path(p), win.destroy()),
            ).pack(side="right", padx=8, pady=8)

        # center-ish
        win.update_idletasks()
        win.geometry(
            "+%d+%d" % (self.winfo_rootx() + 140, self.winfo_rooty() + 120)
        )

    def load_from_path(self, path):
        state = load_draft(path)
        if state:
            self.set_state(state)

    def on_preview_pdf(self):
        """Render current invoice to a temporary PDF and open it."""
        state = self.get_state()
        settings = load_settings() or {}

        tmp = tempfile.NamedTemporaryFile(
            prefix="InvoiceMint-preview-",
            suffix=".pdf",
            delete=False,
        )
        tmp_path = tmp.name
        tmp.close()

        generate_invoice_pdf(state, settings, tmp_path)
        self._open_file(tmp_path)

    def on_export_pdf(self):
        state = self.get_state()
        settings = load_settings() or {}
        default_name = (
            f"Invoice-{state['meta']['number'] or datetime.now().strftime('%Y%m%d-%H%M%S')}.pdf"
        )
        path = filedialog.asksaveasfilename(
            title="Export PDF",
            defaultextension=".pdf",
            initialfile=default_name,
            filetypes=[("PDF", "*.pdf")],
        )
        if not path:
            return

        generate_invoice_pdf(state, settings, path)

        # bump invoice sequence in settings (max of current seq and this number + 1)
        try:
            num = int(state["meta"]["number"] or "0")
        except Exception:
            num = int(settings.get("invoice_seq", 1001))
        next_seq = max(int(settings.get("invoice_seq", 1001)), num) + 1
        settings["invoice_seq"] = next_seq
        save_settings(settings)
        self.inv_no_var.set(str(next_seq))  # preload for next invoice

        toast = ctk.CTkToplevel(self)
        toast.title("Exported")
        ctk.CTkLabel(toast, text=f"Saved: {path}").pack(padx=16, pady=16)
        toast.geometry(
            "+%d+%d" % (self.winfo_rootx() + 120, self.winfo_rooty() + 80)
        )
        toast.after(1600, toast.destroy)
