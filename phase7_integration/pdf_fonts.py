"""
Font management and Indic Unicode typography helper for ReportLab PDF generation.
Registers Tamil, Hindi, and English compatible TrueType fonts.
"""

import logging
import os
from typing import Optional, Tuple

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

logger = logging.getLogger(__name__)

_REGISTERED_FONT: Optional[str] = None
_REGISTERED_BOLD_FONT: Optional[str] = None


def get_available_indic_fonts() -> Tuple[str, str]:
    """
    Locates and registers a TrueType font supporting Tamil, Hindi, and Latin scripts.
    Returns (regular_font_name, bold_font_name).
    Falls back to ('Helvetica', 'Helvetica-Bold') if no Indic font is present.
    """
    global _REGISTERED_FONT, _REGISTERED_BOLD_FONT
    if _REGISTERED_FONT:
        return _REGISTERED_FONT, _REGISTERED_BOLD_FONT

    candidate_paths = [
        os.environ.get("AGRI_INDIC_FONT_PATH"),
        os.path.join(os.path.dirname(__file__), "..", "data", "fonts", "NotoSansTamil-Regular.ttf"),
        # Windows system fonts
        r"C:\Windows\Fonts\Nirmala.ttc",
        r"C:\Windows\Fonts\NirmalaB.ttc",
        r"C:\Windows\Fonts\Latha.ttf",
        r"C:\Windows\Fonts\Vijaya.ttf",
        # Linux / Container system fonts
        "/usr/share/fonts/truetype/noto/NotoSansTamil-Regular.ttf",
        "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Regular.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
    ]

    for p in candidate_paths:
        if p and os.path.isfile(p):
            try:
                if p.lower().endswith(".ttc"):
                    regular = TTFont("AgriIndicFont", p, subfontIndex=0)
                    pdfmetrics.registerFont(regular)
                    _REGISTERED_FONT = "AgriIndicFont"
                    _REGISTERED_BOLD_FONT = "AgriIndicFont"
                    logger.info(f"Registered Indic TTC font from: {p}")
                    return _REGISTERED_FONT, _REGISTERED_BOLD_FONT
                else:
                    regular = TTFont("AgriIndicFont", p)
                    pdfmetrics.registerFont(regular)
                    _REGISTERED_FONT = "AgriIndicFont"
                    _REGISTERED_BOLD_FONT = "AgriIndicFont"
                    logger.info(f"Registered Indic TTF font from: {p}")
                    return _REGISTERED_FONT, _REGISTERED_BOLD_FONT
            except Exception as e:
                logger.warning(f"Failed to register font at {p}: {e}")

    # Fallback to standard ReportLab Type-1 Helvetica
    logger.info("No Indic TrueType font found on host. Falling back to Helvetica.")
    _REGISTERED_FONT = "Helvetica"
    _REGISTERED_BOLD_FONT = "Helvetica-Bold"
    return _REGISTERED_FONT, _REGISTERED_BOLD_FONT


def sanitize_text_for_pdf(text: Optional[str], font_name: str) -> str:
    """
    Ensures text is safely printable with the chosen font.
    If Helvetica is used and Indic characters are present, transliterates or replaces to prevent crash.
    """
    if not text:
        return ""
    s = str(text)
    if font_name in ("Helvetica", "Helvetica-Bold"):
        # Check if non-ASCII characters exist that Helvetica cannot render
        try:
            s.encode("latin-1")
            return s
        except UnicodeEncodeError:
            # Transliterate or clean to prevent PDF build crash
            return s.encode("ascii", "replace").decode("ascii")
    return s
