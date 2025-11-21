from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics

# ---------- text helpers ----------
def _draw_text(c, x, y, text, size=10, bold=False):
    c.setFont("Helvetica-Bold" if bold else "Helvetica", size)
    c.drawString(x, y, text or "")

def _draw_rtext(c, x, y, text, size=10, bold=False):
    c.setFont("Helvetica-Bold" if bold else "Helvetica", size)
    c.drawRightString(x, y, text or "")

def _fit_rtext(c, right_x, y, text, max_width, base_size=10, bold=False, min_size=8):
    """
    Right-aligned text that auto-shrinks if it would exceed max_width.
    """
    s = base_size
    font = "Helvetica-Bold" if bold else "Helvetica"
    while s >= min_size:
        w = pdfmetrics.stringWidth(text or "", font, s)
        if w <= max_width:
            c.setFont(font, s)
            c.drawRightString(right_x, y, text or "")
            return
        s -= 0.5
    # If still too big, clip left
    c.setFont(font, min_size)
    c.drawRightString(right_x, y, text or "")

def _wrap_lines(text, font_name, font_size, max_width):
    """Word-wrap that preserves explicit newlines."""
    if text is None:
        return [""]
    paragraphs = text.splitlines() or [""]
    lines = []
    for para in paragraphs:
        words = para.split()
        if not words:
            lines.append("")  # keep blank line
            continue
        line = ""
        for w in words:
            test = w if not line else f"{line} {w}"
            if pdfmetrics.stringWidth(test, font_name, font_size) <= max_width:
                line = test
            else:
                lines.append(line)
                line = w
        if line:
            lines.append(line)
    return lines or [""]

# ---------- main ----------
def generate_invoice_pdf(state: dict, settings: dict, out_path: str):
    company = (settings or {}).get("company", {})
    client  = (state or {}).get("client", {}) or {}
    meta    = (state or {}).get("meta", {}) or {}
    doc_title = "Invoice" if state.get("kind") == "invoice" else "Quote"

    c = canvas.Canvas(out_path, pagesize=A4)
    c.setTitle(doc_title)

    PAGE_W, PAGE_H = A4
    MARGIN = 18 * mm
    RIGHT_GUTTER = 12 * mm
    CONTENT_R = PAGE_W - MARGIN - RIGHT_GUTTER  # everything aligns to this on the right

    # ====== COLUMN RIGHT-EDGES (numeric columns) ======
    # Define right edges first so we can guarantee spacing + no overlaps.
    GAP = 6 * mm                  # minimum gap between numeric columns
    TOTAL_W = 28 * mm
    TAX_W   = 18 * mm
    UNIT_W  = 26 * mm
    QTY_W   = 14 * mm

    X_TOTAL_R = CONTENT_R
    X_TAX_R   = X_TOTAL_R - GAP - TOTAL_W
    X_UNIT_R  = X_TAX_R   - GAP - TAX_W
    X_QTY_R   = X_UNIT_R  - GAP - UNIT_W

    # Left columns (textual)
    SERVICE_W = 40 * mm
    X_SERVICE_L = MARGIN
    X_DESC_L    = X_SERVICE_L + SERVICE_W
    DESC_MAX_R  = X_QTY_R - GAP              # description must end before Qty column gap
    DESC_MAX_W  = max(20, DESC_MAX_R - X_DESC_L)  # wrap width

    # ====== HEADER BAR ======
    c.setFillColor(colors.HexColor("#1F2937"))
    c.rect(0, PAGE_H - 30*mm, PAGE_W, 30*mm, stroke=0, fill=1)
    c.setFillColor(colors.white)
    _draw_text(c, MARGIN, PAGE_H - 20*mm, "InvoiceMint", size=16, bold=True)
    _draw_rtext(c, CONTENT_R, PAGE_H - 20*mm, doc_title, size=14, bold=True)
    c.setFillColor(colors.black)

    # ====== COMPANY BLOCK (logo + info) ======
    y_top = PAGE_H - 40*mm
    logo_path = company.get("logo_path")
    left_x = MARGIN
    logo_w = logo_h = 25 * mm

    if logo_path and Path(logo_path).exists():
        try:
            img = ImageReader(logo_path)
            c.drawImage(img, MARGIN, y_top - logo_h + 5, width=logo_w, height=logo_h,
                        preserveAspectRatio=True, mask='auto')
            left_x = MARGIN + logo_w + 6*mm
        except Exception:
            left_x = MARGIN

    name = company.get("name", "")
    lines = [company.get("address"), company.get("email"), company.get("phone"), company.get("website")]
    _draw_text(c, left_x, y_top + 8, name, size=12, bold=True)
    y_info = y_top - 8
    for t in filter(None, lines):
        _draw_text(c, left_x, y_info, t); y_info -= 12

    # ====== RIGHT COLUMN: Invoice Details + Bill To ======
    right_w = 74 * mm
    right_x = CONTENT_R - right_w
    y_right = PAGE_H - 40*mm

    _draw_text(c, right_x, y_right, f"{doc_title} Details", size=12, bold=True)
    y_right -= 16
    for line in [
        f"Invoice #: {meta.get('number','')}",
        f"Date: {meta.get('date','')}",
        f"Due: {meta.get('due_date','')}" + (f"  ({meta.get('terms')})" if meta.get('terms') else ""),
    ]:
        _draw_text(c, right_x, y_right, line); y_right -= 12

    y_right -= 10
    _draw_text(c, right_x, y_right, "Bill To", size=12, bold=True); y_right -= 14
    for t in filter(None, [
        client.get("business") or client.get("name"),
        client.get("address"),
        client.get("email"),
        client.get("phone"),
    ]):
        _draw_text(c, right_x, y_right, t); y_right -= 12

    # ====== TABLE HEADER ======
    table_top = min(y_info, y_right) - 10*mm
    c.setStrokeColor(colors.HexColor("#E5E7EB"))
    c.line(MARGIN, table_top, CONTENT_R, table_top)

    c.setFillColor(colors.HexColor("#374151"))
    # Left headers
    _draw_text (c, X_SERVICE_L,             table_top - 12, "Service / Item", bold=True)
    _draw_text (c, X_DESC_L,                table_top - 12, "Description",    bold=True)
    # Right headers (right-aligned to their right-edges)
    _draw_rtext(c, X_QTY_R,                 table_top - 12, "Qty",            bold=True)
    _draw_rtext(c, X_UNIT_R,                table_top - 12, "Unit",           bold=True)
    _draw_rtext(c, X_TAX_R,                 table_top - 12, "Tax %",          bold=True)
    _draw_rtext(c, X_TOTAL_R,               table_top - 12, "Total",          bold=True)
    c.setFillColor(colors.black)

    # ====== ITEMS ======
    line_y = table_top - 26
    FONT = "Helvetica"; SIZE = 10; LINE_H = 14
    TOTAL_BOX_H = 30 * mm
    SAFE_FOOTER_Y = (30 * mm) + TOTAL_BOX_H + (8 * mm)

    for it in state.get("items", []):
        service = it.get("service", "")
        desc    = it.get("description", "") or ""
        qty     = float(it.get("qty", 0) or 0)
        unit    = float(it.get("unit_price", 0) or 0)
        tax     = float(it.get("tax_pct", 0) or 0)
        total   = qty * unit * (1 + tax/100.0)

        # Wrap description to the allowed width, preserving newlines
        desc_lines = _wrap_lines(desc, FONT, SIZE, DESC_MAX_W)
        row_height = max(LINE_H, len(desc_lines) * LINE_H)

        # page break if needed
        if line_y - row_height < SAFE_FOOTER_Y:
            c.showPage()
            # Recompute CONTENT_R on new page (same here, but explicit for clarity)
            _draw_text (c, X_SERVICE_L,  A4[1] - MARGIN - 12, "Service / Item", bold=True)
            _draw_text (c, X_DESC_L,     A4[1] - MARGIN - 12, "Description",    bold=True)
            _draw_rtext(c, X_QTY_R,      A4[1] - MARGIN - 12, "Qty",            bold=True)
            _draw_rtext(c, X_UNIT_R,     A4[1] - MARGIN - 12, "Unit",           bold=True)
            _draw_rtext(c, X_TAX_R,      A4[1] - MARGIN - 12, "Tax %",          bold=True)
            _draw_rtext(c, X_TOTAL_R,    A4[1] - MARGIN - 12, "Total",          bold=True)
            line_y = A4[1] - MARGIN - 28

        # Left cells
        _draw_text(c, X_SERVICE_L, line_y, service, size=SIZE)
        dy = 0
        for ln in desc_lines:
            _draw_text(c, X_DESC_L, line_y - dy, ln, size=SIZE)
            dy += LINE_H

        # Right numeric cells (right-aligned and auto-shrunk if needed)
        _fit_rtext(c, X_QTY_R,   line_y, f"{qty:g}",     QTY_W,  base_size=SIZE)
        _fit_rtext(c, X_UNIT_R,  line_y, f"{unit:.2f}",  UNIT_W, base_size=SIZE)
        _fit_rtext(c, X_TAX_R,   line_y, f"{tax:.0f}",   TAX_W,  base_size=SIZE)
        _fit_rtext(c, X_TOTAL_R, line_y, f"{total:.2f}", TOTAL_W,base_size=SIZE, bold=False)

        line_y -= row_height + 2

    # ====== TOTALS BOX (aligned with content right edge) ======
    totals = state.get("totals", {})
    box_w = 62 * mm
    box_h = TOTAL_BOX_H
    box_x = CONTENT_R - box_w
    box_y = 24 * mm

    c.setStrokeColor(colors.HexColor("#9CA3AF"))
    c.rect(box_x, box_y, box_w, box_h, stroke=1, fill=0)

    label_x = box_x + 6 * mm
    value_r = box_x + box_w - 6 * mm
    baseline = box_y + box_h - 12

    _draw_text (c, label_x, baseline,          "Subtotal:", bold=True)
    _draw_rtext(c, value_r, baseline,          f"{totals.get('subtotal',0):.2f}", bold=True)
    _draw_text (c, label_x, baseline - 12,     "Tax:")
    _draw_rtext(c, value_r, baseline - 12,     f"{totals.get('tax',0):.2f}")
    _draw_text (c, label_x, box_y + 10,        "Grand Total:", bold=True)
    _draw_rtext(c, value_r, box_y + 10,        f"{totals.get('grand_total',0):.2f}", bold=True)

    c.showPage()
    c.save()
    return out_path
