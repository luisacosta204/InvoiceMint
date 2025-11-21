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
    """Right-aligned text that auto-shrinks if it would exceed max_width."""
    s = base_size
    font = "Helvetica-Bold" if bold else "Helvetica"
    t = "" if text is None else str(text)
    while s >= min_size:
        w = pdfmetrics.stringWidth(t, font, s)
        if w <= max_width:
            c.setFont(font, s)
            c.drawRightString(right_x, y, t)
            return
        s -= 0.5
    c.setFont(font, min_size)
    c.drawRightString(right_x, y, t)

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
    RIGHT_GUTTER = 18 * mm
    CONTENT_R = PAGE_W - MARGIN - RIGHT_GUTTER  # right margin alignment

    # ====== COLUMN RIGHT-EDGES (numeric columns) ======
    # Tight, safe cluster near Total to maximize Description width.
    GAP     = 2 * mm       # minimal safe gap between numeric columns
    TOTAL_W = 28 * mm
    TAX_W   = 12 * mm
    UNIT_W  = 24 * mm
    QTY_W   = 9  * mm

    X_TOTAL_R = CONTENT_R
    X_TAX_R   = X_TOTAL_R - GAP - TOTAL_W
    X_UNIT_R  = X_TAX_R   - GAP - TAX_W
    X_QTY_R   = X_UNIT_R  - GAP - UNIT_W

    # Left columns (textual)
    SERVICE_W  = 36 * mm   # a bit slimmer to gift Description more space
    X_SERVICE_L = MARGIN
    X_DESC_L    = X_SERVICE_L + SERVICE_W
    DESC_MAX_R  = X_QTY_R - GAP                    # description ends before Qty gap
    DESC_MAX_W  = max(20, DESC_MAX_R - X_DESC_L)   # wrap width

    # ====== HEADER BAR ======
    c.setFillColor(colors.HexColor("#1F2937"))
    c.rect(0, PAGE_H - 30*mm, PAGE_W, 30*mm, stroke=0, fill=1)
    c.setFillColor(colors.white)
    _draw_text(c, MARGIN, PAGE_H - 20*mm, "InvoiceMint", size=16, bold=True)
    _draw_rtext(c, CONTENT_R, PAGE_H - 20*mm, doc_title, size=14, bold=True)
    c.setFillColor(colors.black)

    # ====== COMPANY BLOCK ======
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
    raw_lines = [company.get("address"), company.get("email"),
                 company.get("phone"), company.get("website")]
    _draw_text(c, left_x, y_top + 8, name, size=12, bold=True)

    # Right column anchor for details/bill-to
    right_w = 74 * mm
    right_x = CONTENT_R - right_w

    max_line_w = max(10, right_x - left_x - 6*mm)  # room for company text
    y_company = y_top - 8
    for t in filter(None, raw_lines):
        for ln in _wrap_lines(t, "Helvetica", 10, max_line_w):
            _draw_text(c, left_x, y_company, ln)
            y_company -= 12
    y_left_bottom = min(y_company, y_top - logo_h + 5) - 4

    # ====== RIGHT COLUMN ======
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
        client.get("address"), client.get("email")
    ]):
        for ln in _wrap_lines(t, "Helvetica", 10, right_w):
            _draw_text(c, right_x, y_right, ln); y_right -= 12
    if client.get("phone"):
        _draw_text(c, right_x, y_right, client.get("phone")); y_right -= 12

    # ====== TABLE HEADER ======
    table_top = min(y_left_bottom, y_right) - 10*mm
    c.setStrokeColor(colors.HexColor("#E5E7EB"))
    c.line(MARGIN, table_top, CONTENT_R, table_top)

    header_y = table_top - 12
    c.setFillColor(colors.HexColor("#374151"))
    # Left headers (fixed)
    _draw_text(c, X_SERVICE_L, header_y, "Service / Item", bold=True)
    _draw_text(c, X_DESC_L,    header_y, "Description",    bold=True)
    # Right headers (use fit to avoid collisions)
    _fit_rtext(c, X_QTY_R,   header_y, "Qty",   QTY_W,  base_size=10, bold=True)
    _fit_rtext(c, X_UNIT_R,  header_y, "Unit",  UNIT_W, base_size=10, bold=True)
    _fit_rtext(c, X_TAX_R,   header_y, "Tax %", TAX_W,  base_size=10, bold=True)
    _fit_rtext(c, X_TOTAL_R, header_y, "Total", TOTAL_W, base_size=10, bold=True)
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

        desc_lines = _wrap_lines(desc, FONT, SIZE, DESC_MAX_W)
        row_height = max(LINE_H, len(desc_lines) * LINE_H)

        if line_y - row_height < SAFE_FOOTER_Y:
            c.showPage()
            # quick header on new page
            nh = A4[1] - MARGIN - 12
            _draw_text(c, X_SERVICE_L, nh, "Service / Item", bold=True)
            _draw_text(c, X_DESC_L,    nh, "Description",    bold=True)
            _fit_rtext(c, X_QTY_R,   nh, "Qty",   QTY_W,  base_size=10, bold=True)
            _fit_rtext(c, X_UNIT_R,  nh, "Unit",  UNIT_W, base_size=10, bold=True)
            _fit_rtext(c, X_TAX_R,   nh, "Tax %", TAX_W,  base_size=10, bold=True)
            _fit_rtext(c, X_TOTAL_R, nh, "Total", TOTAL_W, base_size=10, bold=True)
            line_y = A4[1] - MARGIN - 28

        _draw_text(c, X_SERVICE_L, line_y, service, size=SIZE)
        dy = 0
        for ln in desc_lines:
            _draw_text(c, X_DESC_L, line_y - dy, ln, size=SIZE)
            dy += LINE_H

        _fit_rtext(c, X_QTY_R,   line_y, f"{qty:g}",     QTY_W,  base_size=SIZE)
        _fit_rtext(c, X_UNIT_R,  line_y, f"{unit:.2f}",  UNIT_W, base_size=SIZE)
        _fit_rtext(c, X_TAX_R,   line_y, f"{tax:.0f}",   TAX_W,  base_size=SIZE)
        _fit_rtext(c, X_TOTAL_R, line_y, f"{total:.2f}", TOTAL_W, base_size=SIZE)

        line_y -= row_height + 2

    # ====== TOTALS BOX ======
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

    _draw_text (c, label_x, baseline,      "Subtotal:", bold=True)
    _draw_rtext(c, value_r, baseline,      f"{totals.get('subtotal',0):.2f}", bold=True)
    _draw_text (c, label_x, baseline-12,   "Tax:")
    _draw_rtext(c, value_r, baseline-12,   f"{totals.get('tax',0):.2f}")
    _draw_text (c, label_x, box_y+10,      "Grand Total:", bold=True)
    _draw_rtext(c, value_r, box_y+10,      f"{totals.get('grand_total',0):.2f}", bold=True)

    c.showPage()
    c.save()
    return out_path
