import io

import qrcode
from flask import current_app
from qrcode.constants import ERROR_CORRECT_Q
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.utils import simpleSplit
from reportlab.pdfgen import canvas

LABEL_WIDTH = 80 * mm
LABEL_HEIGHT = 40 * mm
QR_SIZE = 32 * mm
PAGE_PADDING = 2 * mm
SHEET_COLUMNS = 2
SHEET_ROWS = 6
SHEET_GAP = 4 * mm
FONT = "Helvetica"
FONT_BOLD = "Helvetica-Bold"
NAME_MAX_LINES = 4


def build_qr_url(machine):
    base = current_app.config["PUBLIC_BASE_URL"].rstrip("/")
    return f"{base}/machine/{machine.machine_code}?v={machine.qr_version}"


def make_qr(url):
    qr = qrcode.QRCode(error_correction=ERROR_CORRECT_Q, box_size=16, border=4)
    qr.add_data(url)
    qr.make(fit=True)
    return qr


def png_bytes(machine):
    image = make_qr(build_qr_url(machine)).make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def _latin(text):
    return text.encode("latin-1", "replace").decode("latin-1")


def _draw_qr(pdf, qr, x, y, size):
    matrix = qr.get_matrix()
    count = len(matrix)
    module = size / count
    overlap = 0.15
    pdf.setFillColorRGB(0, 0, 0)
    for row_index, row in enumerate(matrix):
        row_top = y + size - row_index * module
        column = 0
        while column < count:
            if not row[column]:
                column += 1
                continue
            start = column
            while column < count and row[column]:
                column += 1
            pdf.rect(
                x + start * module,
                row_top - module - overlap,
                (column - start) * module,
                module + overlap,
                stroke=0,
                fill=1,
            )


def _draw_label(pdf, machine, x, y):
    pdf.setLineWidth(0.5)
    pdf.setStrokeColorRGB(0.6, 0.6, 0.6)
    pdf.roundRect(x, y, LABEL_WIDTH, LABEL_HEIGHT, 2 * mm, stroke=1, fill=0)

    _draw_qr(pdf, make_qr(build_qr_url(machine)), x + 3 * mm, y + (LABEL_HEIGHT - QR_SIZE) / 2, QR_SIZE)

    text_x = x + 3 * mm + QR_SIZE + 3 * mm
    text_width = LABEL_WIDTH - (text_x - x) - 3 * mm
    pdf.setFillColorRGB(0.06, 0.12, 0.23)
    pdf.setFont(FONT_BOLD, 18)
    pdf.drawString(text_x, y + LABEL_HEIGHT - 12 * mm, machine.machine_code)

    pdf.setFont(FONT, 9)
    lines = simpleSplit(_latin(machine.name), FONT, 9, text_width)
    if len(lines) > NAME_MAX_LINES:
        lines = lines[:NAME_MAX_LINES]
        lines[-1] = lines[-1].rstrip()[:-3] + "..."
    cursor = y + LABEL_HEIGHT - 18 * mm
    for line in lines:
        pdf.drawString(text_x, cursor, line)
        cursor -= 11

    pdf.setFont(FONT, 6.5)
    pdf.setFillColorRGB(0.4, 0.4, 0.4)
    pdf.drawString(text_x, y + 4 * mm, "Scan to open machine profile")


def label_pdf_bytes(machine):
    buffer = io.BytesIO()
    page = (LABEL_WIDTH + 2 * PAGE_PADDING, LABEL_HEIGHT + 2 * PAGE_PADDING)
    pdf = canvas.Canvas(buffer, pagesize=page)
    pdf.setTitle(f"QR label {machine.machine_code}")
    pdf.setAuthor("MachineQR")
    _draw_label(pdf, machine, PAGE_PADDING, PAGE_PADDING)
    pdf.save()
    return buffer.getvalue()


def sheet_pdf_bytes(machines):
    buffer = io.BytesIO()
    page_width, page_height = A4
    pdf = canvas.Canvas(buffer, pagesize=A4)
    pdf.setTitle("MachineQR labels")
    pdf.setAuthor("MachineQR")

    grid_width = SHEET_COLUMNS * LABEL_WIDTH + (SHEET_COLUMNS - 1) * SHEET_GAP
    grid_height = SHEET_ROWS * LABEL_HEIGHT + (SHEET_ROWS - 1) * SHEET_GAP
    margin_x = (page_width - grid_width) / 2
    margin_y = (page_height - grid_height) / 2
    per_page = SHEET_COLUMNS * SHEET_ROWS

    for index, machine in enumerate(machines):
        slot = index % per_page
        if index and slot == 0:
            pdf.showPage()
        column = slot % SHEET_COLUMNS
        row = slot // SHEET_COLUMNS
        x = margin_x + column * (LABEL_WIDTH + SHEET_GAP)
        y = page_height - margin_y - (row + 1) * LABEL_HEIGHT - row * SHEET_GAP
        _draw_label(pdf, machine, x, y)
    pdf.save()
    return buffer.getvalue()
