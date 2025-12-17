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
    while s >= min_size:
        w = pdfmetrics.stringWidth(text or "", font, s)
        if w <= max_width:
            c.setFont(font, s)
            c.drawRightString(right_x, y, text or "")
            return
        s -= 0.5
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

# ---------- watermark helper ----------
def _draw_status_watermark(c, status_text: str):
    """
    Draw a big, light diagonal watermark like PAID / UNPAID / OVERDUE
    centered on the page. Only draws for those three statuses.
    """
    if not status_text:
        return
    text = str(status_text).upper()
    if text not in {"PAID", "UNPAID", "OVERDUE"}:
        return

    PAGE_W, PAGE_H = A4
    c.saveState()
    try:
        # very light gray; subtle but visible
        c.setFillColor(colors.Color(0.9, 0.9, 0.9))
        c.setFont("Helvetica-Bold", 72)
        c.translate(PAGE_W / 2.0, PAGE_H / 2.0)
        c.rotate(30)
        c.drawCentredString(0, 0, text)
    finally:
        c.restoreState()

# ---------- public entry ----------
def generate_invoice_pdf(state: dict, settings: dict, out_path: str):
    """
    Public entry: choose template based on settings["pdf"]["template"].

    - "Modern"  => _generate_invoice_pdf_modern
    - "Compact" => _generate_invoice_pdf_compact
    - "Minimal" => _generate_invoice_pdf_minimal
    """
    pdf_cfg = (settings or {}).get("pdf") or {}
    template = (pdf_cfg.get("template") or "Modern").lower()

    if template == "compact":
        return _generate_invoice_pdf_compact(state, settings, out_path)
    elif template == "minimal":
        return _generate_invoice_pdf_minimal(state, settings, out_path)
    else:
        return _generate_invoice_pdf_modern(state, settings, out_path)

# ============================================================
# MODERN template implementation
# ============================================================
def _generate_invoice_pdf_modern(state: dict, settings: dict, out_path: str):
    company = (settings or {}).get("company", {})
    client  = (state or {}).get("client", {}) or {}
    meta    = (state or {}).get("meta", {}) or {}

    # Use doc_type if present; fall back to kind/invoice
    doc_type  = (state or {}).get("doc_type") or ("invoice" if state.get("kind") == "invoice" else "quote")
    doc_title = "Quote" if str(doc_type).lower() == "quote" else "Invoice"

    c = canvas.Canvas(out_path, pagesize=A4)
    c.setTitle(doc_title)

    PAGE_W, PAGE_H = A4
    MARGIN = 18 * mm
    RIGHT_GUTTER = 18 * mm
    CONTENT_R = PAGE_W - MARGIN - RIGHT_GUTTER  # right margin alignment

    # Status watermark on first page
    status = (meta.get("status") or "").upper()
    _draw_status_watermark(c, status)

    # ====== COLUMN RIGHT-EDGES (numeric columns) ======
    GAP     = 6 * mm      # base gap
    TOTAL_W = 28 * mm
    TAX_W   = 12 * mm
    UNIT_W  = 26 * mm
    QTY_W   = 9 * mm

    OFF_TAX  = 3 * mm
    OFF_UNIT = 3 * mm
    OFF_QTY  = 5 * mm

    X_TOTAL_R = CONTENT_R
    X_TAX_R   = X_TOTAL_R - (GAP + TOTAL_W) + OFF_TAX
    X_UNIT_R  = X_TAX_R   - (GAP + TAX_W)  + OFF_UNIT
    X_QTY_R   = X_UNIT_R  - (GAP + UNIT_W) + OFF_QTY

    SERVICE_W  = 40 * mm
    X_SERVICE_L = MARGIN
    X_DESC_L    = X_SERVICE_L + SERVICE_W
    DESC_MAX_R  = X_QTY_R - GAP
    DESC_MAX_W  = max(20, DESC_MAX_R - X_DESC_L)

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
    raw_lines = [company.get("address"), company.get("email"), company.get("phone"), company.get("website")]
    _draw_text(c, left_x, y_top + 8, name, size=12, bold=True)
    right_w   = 74 * mm
    right_x   = CONTENT_R - right_w
    max_line_w = max(10, right_x - left_x - 6*mm)

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

    status_label = meta.get("status") or ""
    lines = [
        f"{doc_title} #: {meta.get('number','')}",
        f"Date: {meta.get('date','')}",
        f"Due: {meta.get('due_date','')}" + (f"  ({meta.get('terms')})" if meta.get('terms') else ""),
    ]
    if status_label:
        lines.append(f"Status: {status_label}")

    for line in lines:
        _draw_text(c, right_x, y_right, line); y_right -= 12

    y_right -= 10
    _draw_text(c, right_x, y_right, "Bill To", size=12, bold=True); y_right -= 14
    for t in filter(None, [
        client.get("business") or client.get("name"),
        client.get("address"),
        client.get("email"),
    ]):
        for ln in _wrap_lines(t, "Helvetica", 10, right_w):
            _draw_text(c, right_x, y_right, ln); y_right -= 12
    if client.get("phone"):
        _draw_text(c, right_x, y_right, client.get("phone")); y_right -= 12

    # ====== TABLE HEADER ======
    table_top = min(y_left_bottom, y_right) - 10*mm
    c.setStrokeColor(colors.HexColor("#E5E7EB"))
    c.line(MARGIN, table_top, CONTENT_R, table_top)
    c.setFillColor(colors.HexColor("#374151"))
    _draw_text (c, X_SERVICE_L, table_top - 12, "Service / Item", bold=True)
    _draw_text (c, X_DESC_L,    table_top - 12, "Description",    bold=True)
    _draw_rtext(c, X_QTY_R,     table_top - 12, "Qty",            bold=True)
    _draw_rtext(c, X_UNIT_R,    table_top - 12, "Unit",           bold=True)
    _draw_rtext(c, X_TAX_R,     table_top - 12, "Tax %",          bold=True)
    _draw_rtext(c, X_TOTAL_R,   table_top - 12, "Total",          bold=True)
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
            # watermark on subsequent pages
            _draw_status_watermark(c, status)

            _draw_text (c, X_SERVICE_L,  A4[1] - MARGIN - 12, "Service / Item", bold=True)
            _draw_text (c, X_DESC_L,     A4[1] - MARGIN - 12, "Description",    bold=True)
            _draw_rtext(c, X_QTY_R,      A4[1] - MARGIN - 12, "Qty",            bold=True)
            _draw_rtext(c, X_UNIT_R,     A4[1] - MARGIN - 12, "Unit",           bold=True)
            _draw_rtext(c, X_TAX_R,      A4[1] - MARGIN - 12, "Tax %",          bold=True)
            _draw_rtext(c, X_TOTAL_R,    A4[1] - MARGIN - 12, "Total",          bold=True)
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

# ============================================================
# COMPACT template (denser: smaller fonts, tighter rows)
# ============================================================
def _generate_invoice_pdf_compact(state: dict, settings: dict, out_path: str):
    company = (settings or {}).get("company", {})
    client  = (state or {}).get("client", {}) or {}
    meta    = (state or {}).get("meta", {}) or {}

    doc_type  = (state or {}).get("doc_type") or ("invoice" if state.get("kind") == "invoice" else "quote")
    doc_title = "Quote" if str(doc_type).lower() == "quote" else "Invoice"

    c = canvas.Canvas(out_path, pagesize=A4)
    c.setTitle(doc_title)

    PAGE_W, PAGE_H = A4
    MARGIN = 16 * mm   # slightly smaller
    RIGHT_GUTTER = 16 * mm
    CONTENT_R = PAGE_W - MARGIN - RIGHT_GUTTER

    # Status watermark on first page
    status = (meta.get("status") or "").upper()
    _draw_status_watermark(c, status)

    GAP     = 6 * mm
    TOTAL_W = 28 * mm
    TAX_W   = 12 * mm
    UNIT_W  = 26 * mm
    QTY_W   = 9 * mm

    OFF_TAX  = 3 * mm
    OFF_UNIT = 3 * mm
    OFF_QTY  = 5 * mm

    X_TOTAL_R = CONTENT_R
    X_TAX_R   = X_TOTAL_R - (GAP + TOTAL_W) + OFF_TAX
    X_UNIT_R  = X_TAX_R   - (GAP + TAX_W)  + OFF_UNIT
    X_QTY_R   = X_UNIT_R  - (GAP + UNIT_W) + OFF_QTY

    SERVICE_W  = 40 * mm
    X_SERVICE_L = MARGIN
    X_DESC_L    = X_SERVICE_L + SERVICE_W
    DESC_MAX_R  = X_QTY_R - GAP
    DESC_MAX_W  = max(20, DESC_MAX_R - X_DESC_L)

    # Header (smaller, darker)
    c.setFillColor(colors.HexColor("#111827"))
    c.rect(0, PAGE_H - 26*mm, PAGE_W, 26*mm, stroke=0, fill=1)
    c.setFillColor(colors.white)
    _draw_text(c, MARGIN, PAGE_H - 18*mm, "InvoiceMint", size=14, bold=True)
    _draw_rtext(c, CONTENT_R, PAGE_H - 18*mm, doc_title, size=12, bold=True)
    c.setFillColor(colors.black)

    # Company
    y_top = PAGE_H - 36*mm
    logo_path = company.get("logo_path")
    left_x = MARGIN
    logo_w = logo_h = 22 * mm
    if logo_path and Path(logo_path).exists():
        try:
            img = ImageReader(logo_path)
            c.drawImage(img, MARGIN, y_top - logo_h + 4, width=logo_w, height=logo_h,
                        preserveAspectRatio=True, mask='auto')
            left_x = MARGIN + logo_w + 5*mm
        except Exception:
            left_x = MARGIN

    name = company.get("name", "")
    raw_lines = [company.get("address"), company.get("email"), company.get("phone"), company.get("website")]
    _draw_text(c, left_x, y_top + 6, name, size=11, bold=True)
    right_w   = 72 * mm
    right_x   = CONTENT_R - right_w
    max_line_w = max(10, right_x - left_x - 6*mm)

    y_company = y_top - 6
    for t in filter(None, raw_lines):
        for ln in _wrap_lines(t, "Helvetica", 9, max_line_w):
            _draw_text(c, left_x, y_company, ln, size=9)
            y_company -= 11
    y_left_bottom = min(y_company, y_top - logo_h + 4) - 3

    # Right column
    y_right = PAGE_H - 36*mm
    _draw_text(c, right_x, y_right, f"{doc_title} Details", size=11, bold=True)
    y_right -= 14

    status_label = meta.get("status") or ""
    lines = [
        f"{doc_title} #: {meta.get('number','')}",
        f"Date: {meta.get('date','')}",
        f"Due: {meta.get('due_date','')}" + (f"  ({meta.get('terms')})" if meta.get('terms') else ""),
    ]
    if status_label:
        lines.append(f"Status: {status_label}")

    for line in lines:
        _draw_text(c, right_x, y_right, line, size=9); y_right -= 11

    y_right -= 8
    _draw_text(c, right_x, y_right, "Bill To", size=11, bold=True); y_right -= 12
    for t in filter(None, [
        client.get("business") or client.get("name"),
        client.get("address"),
        client.get("email"),
    ]):
        for ln in _wrap_lines(t, "Helvetica", 9, right_w):
            _draw_text(c, right_x, y_right, ln, size=9); y_right -= 11
    if client.get("phone"):
        _draw_text(c, right_x, y_right, client.get("phone"), size=9); y_right -= 11

    # Table header
    table_top = min(y_left_bottom, y_right) - 8*mm
    c.setStrokeColor(colors.HexColor("#E5E7EB"))
    c.line(MARGIN, table_top, CONTENT_R, table_top)
    c.setFillColor(colors.HexColor("#374151"))
    _draw_text (c, X_SERVICE_L, table_top - 11, "Service / Item", size=9, bold=True)
    _draw_text (c, X_DESC_L,    table_top - 11, "Description",    size=9, bold=True)
    _draw_rtext(c, X_QTY_R,     table_top - 11, "Qty",            size=9, bold=True)
    _draw_rtext(c, X_UNIT_R,    table_top - 11, "Unit",           size=9, bold=True)
    _draw_rtext(c, X_TAX_R,     table_top - 11, "Tax %",          size=9, bold=True)
    _draw_rtext(c, X_TOTAL_R,   table_top - 11, "Total",          size=9, bold=True)
    c.setFillColor(colors.black)

    # Items
    line_y = table_top - 22
    FONT = "Helvetica"; SIZE = 9; LINE_H = 12
    TOTAL_BOX_H = 24 * mm
    SAFE_FOOTER_Y = (26 * mm) + TOTAL_BOX_H + (6 * mm)

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
            # watermark on subsequent pages
            _draw_status_watermark(c, status)

            top_y = A4[1] - MARGIN - 10
            c.setFillColor(colors.HexColor("#374151"))
            _draw_text (c, X_SERVICE_L, top_y, "Service / Item", size=9, bold=True)
            _draw_text (c, X_DESC_L,    top_y, "Description",    size=9, bold=True)
            _draw_rtext(c, X_QTY_R,     top_y, "Qty",            size=9, bold=True)
            _draw_rtext(c, X_UNIT_R,    top_y, "Unit",           size=9, bold=True)
            _draw_rtext(c, X_TAX_R,     top_y, "Tax %",          size=9, bold=True)
            _draw_rtext(c, X_TOTAL_R,   top_y, "Total",          size=9, bold=True)
            c.setFillColor(colors.black)
            line_y = top_y - 18

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

    # Totals box
    totals = state.get("totals", {})
    box_w = 60 * mm
    box_h = TOTAL_BOX_H
    box_x = CONTENT_R - box_w
    box_y = 22 * mm
    c.setStrokeColor(colors.HexColor("#9CA3AF"))
    c.rect(box_x, box_y, box_w, box_h, stroke=1, fill=0)
    label_x = box_x + 5 * mm
    value_r = box_x + box_w - 5 * mm
    baseline = box_y + box_h - 11
    _draw_text (c, label_x, baseline,      "Subtotal:", size=9, bold=True)
    _draw_rtext(c, value_r, baseline,      f"{totals.get('subtotal',0):.2f}", size=9, bold=True)
    _draw_text (c, label_x, baseline-11,   "Tax:",      size=9)
    _draw_rtext(c, value_r, baseline-11,   f"{totals.get('tax',0):.2f}", size=9)
    _draw_text (c, label_x, box_y+8,       "Grand Total:", size=9, bold=True)
    _draw_rtext(c, value_r, box_y+8,       f"{totals.get('grand_total',0):.2f}", size=9, bold=True)

    c.showPage()
    c.save()
    return out_path

# ============================================================
# MINIMAL template (clean, no dark bar, lots of white)
# ============================================================
def _generate_invoice_pdf_minimal(state: dict, settings: dict, out_path: str):
    company = (settings or {}).get("company", {})
    client  = (state or {}).get("client", {}) or {}
    meta    = (state or {}).get("meta", {}) or {}
    notes   = (state or {}).get("notes", "") or ""

    doc_type  = (state or {}).get("doc_type") or ("invoice" if state.get("kind") == "invoice" else "quote")
    doc_title = "Quote" if str(doc_type).lower() == "quote" else "Invoice"

    c = canvas.Canvas(out_path, pagesize=A4)
    c.setTitle(doc_title)

    PAGE_W, PAGE_H = A4
    MARGIN = 20 * mm
    RIGHT_GUTTER = 20 * mm
    CONTENT_R = PAGE_W - MARGIN - RIGHT_GUTTER

    # Status watermark on first page
    status = (meta.get("status") or "").upper()
    _draw_status_watermark(c, status)

    GAP     = 6 * mm
    TOTAL_W = 28 * mm
    TAX_W   = 12 * mm
    UNIT_W  = 26 * mm
    QTY_W   = 9 * mm

    OFF_TAX  = 3 * mm
    OFF_UNIT = 3 * mm
    OFF_QTY  = 5 * mm

    X_TOTAL_R = CONTENT_R
    X_TAX_R   = X_TOTAL_R - (GAP + TOTAL_W) + OFF_TAX
    X_UNIT_R  = X_TAX_R   - (GAP + TAX_W)  + OFF_UNIT
    X_QTY_R   = X_UNIT_R  - (GAP + UNIT_W) + OFF_QTY

    SERVICE_W  = 40 * mm
    X_SERVICE_L = MARGIN
    X_DESC_L    = X_SERVICE_L + SERVICE_W
    DESC_MAX_R  = X_QTY_R - GAP
    DESC_MAX_W  = max(20, DESC_MAX_R - X_DESC_L)

    # ====== TOP TITLE + COMPANY (no filled bar) ======
    y_top = PAGE_H - 25*mm

    # Left: company + logo
    logo_path = company.get("logo_path")
    left_x = MARGIN
    logo_w = logo_h = 20 * mm
    if logo_path and Path(logo_path).exists():
        try:
            img = ImageReader(logo_path)
            c.drawImage(img, MARGIN, y_top - logo_h + 4, width=logo_w, height=logo_h,
                        preserveAspectRatio=True, mask='auto')
            left_x = MARGIN + logo_w + 5*mm
        except Exception:
            left_x = MARGIN

    name = company.get("name", "")
    raw_lines = [company.get("address"), company.get("email"), company.get("phone"), company.get("website")]

    _draw_text(c, left_x, y_top + 4, name or "InvoiceMint", size=12, bold=True)
    y_company = y_top - 8
    for t in filter(None, raw_lines):
        for ln in _wrap_lines(t, "Helvetica", 9, CONTENT_R - left_x - 10*mm):
            _draw_text(c, left_x, y_company, ln, size=9)
            y_company -= 11

    # Right: big title + meta
    title_y = PAGE_H - 22*mm
    _draw_rtext(c, CONTENT_R, title_y, doc_title.upper(), size=14, bold=True)
    y_meta = title_y - 14

    status_label = meta.get("status") or ""
    meta_lines = [
        f"{doc_title} #: {meta.get('number','')}",
        f"Date: {meta.get('date','')}",
        f"Due: {meta.get('due_date','')}",
    ]
    if status_label:
        meta_lines.append(f"Status: {status_label}")

    for line in meta_lines:
        if line.strip().endswith(": "):
            continue
        _draw_rtext(c, CONTENT_R, y_meta, line, size=9); y_meta -= 11

    # Thin line separating header from body
    c.setStrokeColor(colors.HexColor("#D1D5DB"))
    c.line(MARGIN, y_company - 4, PAGE_W - MARGIN, y_company - 4)

    # ====== BILL TO block (left) ======
    y_bill = y_company - 16
    _draw_text(c, MARGIN, y_bill, "Bill To", size=11, bold=True)
    y_bill -= 12
    bill_lines = [
        client.get("business") or client.get("name"),
        client.get("address"),
        client.get("email"),
        client.get("phone"),
    ]
    for t in filter(None, bill_lines):
        for ln in _wrap_lines(t, "Helvetica", 9, 70*mm):
            _draw_text(c, MARGIN, y_bill, ln, size=9); y_bill -= 11

    # Maybe a reference / terms on the right (minimal)
    y_ref = y_company - 16
    if meta.get("terms"):
        _draw_rtext(c, CONTENT_R, y_ref, meta.get("terms", ""), size=9)
        y_ref -= 11

    # ====== TABLE HEADER ======
    table_top = min(y_bill, y_ref) - 10*mm
    c.setStrokeColor(colors.HexColor("#E5E7EB"))
    c.line(MARGIN, table_top, PAGE_W - MARGIN, table_top)
    c.setFillColor(colors.HexColor("#4B5563"))
    _draw_text (c, X_SERVICE_L, table_top - 11, "Service / Item", size=9, bold=True)
    _draw_text (c, X_DESC_L,    table_top - 11, "Description",    size=9, bold=True)
    _draw_rtext(c, X_QTY_R,     table_top - 11, "Qty",            size=9, bold=True)
    _draw_rtext(c, X_UNIT_R,    table_top - 11, "Unit",           size=9, bold=True)
    _draw_rtext(c, X_TAX_R,     table_top - 11, "Tax %",          size=9, bold=True)
    _draw_rtext(c, X_TOTAL_R,   table_top - 11, "Total",          size=9, bold=True)
    c.setFillColor(colors.black)

    # ====== ITEMS ======
    line_y = table_top - 22
    FONT = "Helvetica"; SIZE = 9; LINE_H = 12
    TOTAL_BOX_H = 26 * mm
    SAFE_FOOTER_Y = (26 * mm) + TOTAL_BOX_H + (8 * mm)  # reserved zone at bottom

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
            # watermark on subsequent pages
            _draw_status_watermark(c, status)

            top_y = A4[1] - MARGIN - 12
            c.setStrokeColor(colors.HexColor("#E5E7EB"))
            c.line(MARGIN, top_y + 4, PAGE_W - MARGIN, top_y + 4)
            c.setFillColor(colors.HexColor("#4B5563"))
            _draw_text (c, X_SERVICE_L, top_y, "Service / Item", size=9, bold=True)
            _draw_text (c, X_DESC_L,    top_y, "Description",    size=9, bold=True)
            _draw_rtext(c, X_QTY_R,     top_y, "Qty",            size=9, bold=True)
            _draw_rtext(c, X_UNIT_R,    top_y, "Unit",           size=9, bold=True)
            _draw_rtext(c, X_TAX_R,     top_y, "Tax %",          size=9, bold=True)
            _draw_rtext(c, X_TOTAL_R,   top_y, "Total",          size=9, bold=True)
            c.setFillColor(colors.black)
            line_y = top_y - 18

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

    # ====== NOTES (left side, above totals, with label) ======
    base_y = 26 * mm  # same base used for totals
    if notes.strip():
        notes_label_y = SAFE_FOOTER_Y - 10
        min_y = base_y + 28  # keep a decent gap above the totals line

        # label "Notes:" on the left
        c.setFillColor(colors.HexColor("#6B7280"))
        _draw_text(c, MARGIN, notes_label_y, "Notes:", size=9, bold=True)
        notes_y = notes_label_y - 12

        # wrap notes text to fit from a bit right of the label to the right margin
        notes_text_x = MARGIN + 10 * mm
        notes_lines = _wrap_lines(notes, "Helvetica", 9, CONTENT_R - notes_text_x)

        for ln in notes_lines:
            if notes_y < min_y:
                break
            _draw_text(c, notes_text_x, notes_y, ln, size=9)
            notes_y -= 11
        c.setFillColor(colors.black)

    # ====== TOTALS (inline, no big box) ======
    totals = state.get("totals", {})
    label_x = X_DESC_L
    value_r = CONTENT_R

    # Move the line higher so there is more gap above "Subtotal:"
    c.setStrokeColor(colors.HexColor("#E5E7EB"))
    c.line(MARGIN, base_y + 22, PAGE_W - MARGIN, base_y + 22)

    _draw_text (c, label_x, base_y + 12,  "Subtotal:", size=9, bold=True)
    _draw_rtext(c, value_r, base_y + 12,  f"{totals.get('subtotal',0):.2f}", size=9, bold=True)
    _draw_text (c, label_x, base_y + 0,   "Tax:",      size=9)
    _draw_rtext(c, value_r, base_y + 0,   f"{totals.get('tax',0):.2f}", size=9)
    _draw_text (c, label_x, base_y - 12,  "Grand Total:", size=10, bold=True)
    _draw_rtext(c, value_r, base_y - 12,  f"{totals.get('grand_total',0):.2f}", size=10, bold=True)

    c.showPage()
    c.save()
    return out_path
