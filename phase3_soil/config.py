"""Phase 3 configuration. All paths/limits can be overridden by environment variables."""
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STORAGE_DIR = os.environ.get("SOIL_STORAGE_DIR", os.path.join(BASE_DIR, "private_storage"))  # NOT served statically
DB_PATH = os.environ.get("SOIL_DB_PATH", os.path.join(BASE_DIR, "soil_phase3.sqlite3"))
MAX_UPLOAD_BYTES = int(os.environ.get("SOIL_MAX_UPLOAD_BYTES", 10 * 1024 * 1024))  # 10 MB
MAX_PDF_PAGES = int(os.environ.get("SOIL_MAX_PDF_PAGES", 5))
MAX_IMAGE_PIXELS = 40_000_000
PDF_RENDER_DPI = 300
API_KEY = os.environ.get("SOIL_API_KEY")  # if set, X-API-Key header is required (placeholder for app auth)
# OCR quality heuristics (engineering thresholds, NOT accuracy claims)
LOW_MEAN_WORD_CONF = 55.0   # Tesseract word confidence 0-100
MIN_WORDS_FOR_TEXT = 8
TEST_DATE_STALE_YEARS = 3
