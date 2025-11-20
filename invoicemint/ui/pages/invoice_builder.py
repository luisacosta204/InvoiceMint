# invoicemint/ui/pages/invoice_builder.py
import tkinter as tk
from tkinter import ttk


class InvoiceBuilder(ttk.Frame):
    """
    Main invoice/quote editor.
    - Add/remove line items
    - Auto-calc subtotal, tax, grand total
    """
    def __init__(self, parent, tokens):
        super().__init__(parent, style="Card.TFrame")
        self.tokens = tokens
        self.rows = []
        self._build()

    def restyle(self, tokens):
        # Called by MainApp when theme changes
        self.tokens = tokens

    def _build(self):
        self.grid_columnconfigure(0, weight=1)

        # Header row
        header = ttk.Frame(self, style="Card.TFrame")
        header.grid(row=0, column=0, sticky="ew", padx=12, pady=(12, 0))
        for i, h in enumerate(["Description", "Qty", "Unit Price", "Tax %", "Total", "Remove"]):
            ttk.Label(header, text=h).grid(row=0, column=i, padx=4, pady=6, sticky="w")

        # Body (line items)
        self.body = ttk.Frame(self, style="Card.TFrame")
        self.body.grid(row=1, column=0, sticky="nsew", padx=12)
        self.grid_rowconfigure(1, weight=1)

        # Actions
        actions = ttk.Frame(self, style="Card.TFrame")
        actions.grid(row=2, column=0, pady=(0, 12))
        ttk.Button(actions, text="+ Add Item", command=self.add_row, style="Accent.TButton").grid(row=0, column=0)

        # Totals footer
        totals = ttk.Frame(self, style="Card.TFrame")
        totals.grid(row=3, column=0, sticky="e", padx=12, pady=(0, 12))

        ttk.Label(totals, text="Subtotal:").grid(row=0, column=0, padx=8, sticky="e")
        self.subtotal_var = tk.StringVar(value="0.00")
        ttk.Label(totals, textvariable=self.subtotal_var).grid(row=0, column=1, sticky="e")

        ttk.Label(totals, text="Total Tax:").grid(row=1, column=0, padx=8, sticky="e")
        self.tax_var = tk.StringVar(value="0.00")
        ttk.Label(totals, textvariable=self.tax_var).grid(row=1, column=1, sticky="e")

        ttk.Label(totals, text="Grand Total:", font=("Inter", 12, "bold")).grid(row=2, column=0, padx=8, sticky="e")
        self.total_var = tk.StringVar(value="0.00")
        ttk.Label(totals, textvariable=self.total_var, font=("Inter", 12, "bold")).grid(row=2, column=1, sticky="e")

        # One starter row
        self.add_row()

    # ---------- line item logic ----------
    def add_row(self):
        idx = len(self.rows)
        row = ttk.Frame(self.body, style="Card.TFrame")
        row.grid(row=idx, column=0, sticky="ew", pady=4)

        e_desc = ttk.Entry(row, width=30)
        e_qty = ttk.Entry(row, width=6)
        e_price = ttk.Entry(row, width=10)
        e_tax = ttk.Entry(row, width=6)
        l_total = ttk.Label(row, width=10, text="0.00", anchor="e")
        b_remove = ttk.Button(row, text="✕", command=lambda r=row: self.remove_row(r))

        for i, w in enumerate([e_desc, e_qty, e_price, e_tax, l_total, b_remove]):
            w.grid(row=0, column=i, padx=4)

        for e in (e_qty, e_price, e_tax):
            e.bind("<KeyRelease>", lambda _ev: self.recompute())

        self.rows.append((row, e_desc, e_qty, e_price, e_tax, l_total))
        self.recompute()

    def remove_row(self, row_widget):
        for tup in self.rows:
            if tup[0] == row_widget:
                self.rows.remove(tup)
                row_widget.destroy()
                break
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
