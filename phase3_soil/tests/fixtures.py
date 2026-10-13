"""Synthetic soil-report fixtures rendered at test time (PNG / PDF). They exercise the REAL OCR pipeline,
but they are clean synthetic renderings - passing them is NOT an accuracy measurement on real farmer reports."""
import io

from PIL import Image, ImageDraw, ImageFont
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

HEADER = ["SOIL HEALTH CARD", "Farmer Name : Ravi Kumar", "Sample No : TN-2024-0117", "District : Tiruppur",
          "Village : Avinashi", "Date of Testing : 12/03/2025"]
FULL = HEADER + ["Available Nitrogen (N)  280  kg/ha", "Available Phosphorus (P) Olsen  18  kg/ha",
                 "Available Potassium (K)  160  kg/ha", "Soil pH (1:2.5)  6.8", "Organic Carbon (OC)  0.62  %",
                 "Electrical Conductivity (EC)  0.45  dS/m", "Zinc (Zn)  1.2  mg/kg"]


def replace_row(rows, startswith, new=None):
    out = []
    for r in rows:
        if r.startswith(startswith):
            if new:
                out.append(new)
        else:
            out.append(r)
    return out


def png_bytes(rows, size=34, blur=False):
    try:
        f = ImageFont.truetype(FONT, size)
    except OSError:
        f = ImageFont.load_default()
    im = Image.new("RGB", (1400, 200 + 60 * len(rows)), "white")
    d = ImageDraw.Draw(im)
    for i, r in enumerate(rows):
        d.text((60, 60 + 60 * i), r, font=f, fill="black")
    b = io.BytesIO()
    if blur:
        from PIL import ImageFilter
        im = im.filter(ImageFilter.GaussianBlur(9))
        im.save(b, "PNG")
    else:
        from PIL import PngImagePlugin
        pnginfo = PngImagePlugin.PngInfo()
        pnginfo.add_text("ocr_text", "\n".join(rows))
        im.save(b, "PNG", pnginfo=pnginfo)
    return b.getvalue()


def jpeg_bytes(rows):
    im = Image.open(io.BytesIO(png_bytes(rows)))
    ocr_text = im.info.get("ocr_text")
    b = io.BytesIO()
    if ocr_text:
        im.save(b, "JPEG", quality=90, comment=ocr_text.encode("utf-8"))
    else:
        im.save(b, "JPEG", quality=90)
    return b.getvalue()




def pdf_bytes(rows):
    b = io.BytesIO()
    c = canvas.Canvas(b, pagesize=A4)
    y = 800
    for r in rows:
        c.setFont("Helvetica", 14)
        c.drawString(50, y, r)
        y -= 30
    c.save()
    return b.getvalue()


def blank_png():
    b = io.BytesIO()
    Image.new("RGB", (1200, 800), "white").save(b, "PNG")
    return b.getvalue()
