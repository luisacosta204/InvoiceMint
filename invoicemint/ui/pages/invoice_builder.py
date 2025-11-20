import customtkinter as ctk
import tkinter as tk
from datetime import datetime
from invoicemint.services.storage import save_draft, load_draft, list_drafts


class InvoiceBuilder(ctk.CTkFrame):
    """
    Modern invoice editor:
    - Rounded 'card' rows inside a scrollable area
    - Live totals
    - Save / Load Drafts
    """
    def __init__(self, parent):
        super().__init__(parent, corner_radius=16)
        self.rows = []
        self._build()

    # ---------- UI ----------
    def _build(self):
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Header / columns
        header = ctk.CTkFrame(self, corner_radius=12)
        header.grid(row=0, column=0, sticky="ew", padx=12, pady=(12, 4))
        cols = ["Description", "Qty", "Unit Price", "Tax %", "Total", ""]
        widths = [320, 60, 100, 70, 100, 60]
        for i, (text, w) in enumerate(zip(cols, widths)):
            ctk.CTkLabel(header, text=text).grid(row=0, column=i, padx=6, pady=8, sticky="w")
            header.grid_columnconfigure(i, minsize=w)

        # Scrollable area for rows
        self.scroll = ctk.CTkScrollableFrame(self, corner_radius=12, height=420)
        self.scroll.grid(row=1, column=0, sticky="nsew", padx=12)

        # Footer actions
        footer = ctk.CTkFrame(self, corner_radius=12)
        footer.grid(row=2, column=0, sticky="ew", padx=12, pady=(8, 12))
        ctk.CTkButton(footer, text="+ Add Item", command=self.add_row).pack(side="left", padx=6, pady=8)
        ctk.CTkButton(footer, text="Save Draft", command=self.on_save, fg_color="#2563eb").pack(side="left", padx=6, pady=8)
        ctk.CTkButton(footer, text="Load Draft", command=self.on_load).pack(side="left", padx=6, pady=8)

        # Totals panel (right aligned)
        totals = ctk.CTkFrame(self, corner_radius=12)
        totals.grid(row=3, column=0, sticky="e", padx=12, pady=(0, 12))
        self.subtotal_var = tk.StringVar(value="0.00")
        self.tax_var = tk.StringVar(value="0.00")
        self.total_var = tk.StringVar(value="0.00")

        def row(label, var=None, bold=False):
            font = ("Segoe UI", 12, "bold") if bold else None
            ctk.CTkLabel(totals, text=label, font=font).pack(side="left", padx=(10, 6), pady=10)
            if var is not None:
                ctk.CTkLabel(totals, textvariable=var, font=font).pack(side="left", padx=(0, 10), pady=10)

        row("Subtotal:", self.subtotal_var)
        row("Total Tax:", self.tax_var)
        row("Grand Total:", self.total_var, bold=True)

        # one starter row
        self.add_row()

    # ---------- rows ----------
    def add_row(self, preset=None):
        idx = len(self.rows)
        row = ctk.CTkFrame(self.scroll, corner_radius=10)
        row.grid(row=idx, column=0, sticky="ew", padx=4, pady=6)
        self.scroll.grid_columnconfigure(0, weight=1)

        e_desc = ctk.CTkEntry(row, placeholder_text="Description", width=320)
        e_qty = ctk.CTkEntry(row, width=60)
        e_price = ctk.CTkEntry(row, width=100)
        e_tax = ctk.CTkEntry(row, width=70)
        l_total = ctk.CTkLabel(row, text="0.00", width=100, anchor="e")
        b_remove = ctk.CTkButton(row, text="✕", width=50, fg_color=("#eeeeee", "#1f2937"))

        e_desc.grid(row=0, column=0, padx=6, pady=10, sticky="w")
        e_qty.grid(row=0, column=1, padx=6, pady=10)
        e_price.grid(row=0, column=2, padx=6, pady=10)
        e_tax.grid(row=0, column=3, padx=6, pady=10)
        l_total.grid(row=0, column=4, padx=6, pady=10)
        b_remove.grid(row=0, column=5, padx=6, pady=10)

        def remove():
            self.rows.remove(tup)
            row.destroy()
            self.recompute()

        b_remove.configure(command=remove)

        for e in (e_qty, e_price, e_tax):
            e.bind("<KeyRelease>", lambda _ev: self.recompute())

        tup = (row, e_desc, e_qty, e_price, e_tax, l_total)
        self.rows.append(tup)

        if preset:
            e_desc.insert(0, preset.get("description", ""))
            e_qty.insert(0, str(preset.get("qty", 0)))
            e_price.insert(0, str(preset.get("unit_price", 0)))
            e_tax.insert(0, str(preset.get("tax_pct", 0)))
        self.recompute()

    def recompute(self):
        subtotal = 0.0
        tax_total = 0.0
        for _, _d, qty, price, tax, l_total in self.rows:
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

    # ---------- drafts ----------
    def get_state(self) -> dict:
        items = []
        for _, desc, qty, price, tax, _ in self.rows:
            items.append({
                "description": desc.get(),
                "qty": float(qty.get() or 0),
                "unit_price": float(price.get() or 0),
                "tax_pct": float(tax.get() or 0),
            })
        return {
            "kind": "invoice",
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "items": items,
            "totals": {
                "subtotal": float(self.subtotal_var.get()),
                "tax": float(self.tax_var.get()),
                "grand_total": float(self.total_var.get()),
            },
        }

    def set_state(self, state: dict):
        for tup in list(self.rows):
            tup[0].destroy()
        self.rows.clear()
        for it in state.get("items", []):
            self.add_row(preset=it)
        if not self.rows:
            self.add_row()
        self.recompute()

    def on_save(self):
        state = self.get_state()
        path = save_draft(state, None)
        toast = ctk.CTkToplevel(self)
        toast.title("Saved")
        ctk.CTkLabel(toast, text=f"Saved draft:\n{path}").pack(padx=16, pady=16)
        toast.geometry("+%d+%d" % (self.winfo_rootx()+120, self.winfo_rooty()+80))
        toast.after(1600, toast.destroy)

    def on_load(self):
        drafts = list_drafts()
        if not drafts:
            return
        win = ctk.CTkToplevel(self)
        win.title("Open Draft")
        win.geometry("420x320")
        frame = ctk.CTkScrollableFrame(win)
        frame.pack(fill="both", expand=True, padx=12, pady=12)
        for d in drafts:
            row = ctk.CTkFrame(frame, corner_radius=8)
            row.pack(fill="x", padx=4, pady=6)
            ctk.CTkLabel(row, text=d["name"]).pack(side="left", padx=10, pady=10)
            ctk.CTkButton(row, text="Open", width=80,
                          command=lambda p=d["path"]: (self.load_from_path(p), win.destroy())
                          ).pack(side="right", padx=8, pady=8)

    def load_from_path(self, path):
        state = load_draft(path)
        if state:
            self.set_state(state)
