"""
Coordinate-based extraction of two tables from the Tamil Nadu Season & Crop Reports (SCR):
  * TABLE V-A  District-wise average yield rates of the crops
  * TABLE I-A  District-wise seasonal rainfall
Values are read exactly as printed in the uploaded PDFs; nothing is generated or filled.
Each numeric token is assigned to a column by the x-position of the printed column-number row,
so blank cells (which pdftotext collapses) do not shift values.
"""
import re
import pdfplumber

YIELD_RE = re.compile(r"DISTRICT ?WISE AVERAGE YIELD RATES", re.I)
RAIN_RE = re.compile(r"DISTRICTWISE\s*-\s*SEASONAL RAINFALL", re.I)
FIXED_MISSING_COLS = []
NUM_RE = re.compile(r"^-?\d+(\.\d+)?$")


def _find_pages(pdf, regex):
    """Return 0-based page indexes whose text matches regex (title is at the top of the page)."""
    pages = []
    for i, page in enumerate(pdf.pages):
        txt = (page.crop((0, 0, page.width, page.height * 0.25)).extract_text() or "")
        if regex.search(txt):
            pages.append(i)
    return pages


def _group_rows(words, tol=2.5):
    rows = []
    for w in sorted(words, key=lambda w: (round(w["top"], 1), w["x0"])):
        if rows and abs(rows[-1][0] - w["top"]) <= tol:
            rows[-1][1].append(w)
        else:
            rows.append([w["top"], [w]])
    return [(t, sorted(ws, key=lambda w: w["x0"])) for t, ws in rows]


def _cluster_right_edges(xs, gap=8.0):
    xs = sorted(xs)
    clusters = [[xs[0]]]
    for x in xs[1:]:
        if x - clusters[-1][-1] > gap:
            clusters.append([x])
        else:
            clusters[-1].append(x)
    return [sum(c) / len(c) for c in clusters], [(min(c), max(c)) for c in clusters]


def parse_table_page(page):
    """Return (column_numbers, rows, max_cluster_spread).
    Numbers are right-aligned, so each numeric token is assigned to a column by clustering the
    right edges (x1) of all numeric tokens on the page, then mapping clusters left-to-right onto the
    printed column numbers. If the number of clusters differs from the number of printed columns the
    page is rejected (raises) instead of guessing."""
    words = page.extract_words(keep_blank_chars=False, use_text_flow=False)
    rows = _group_rows(words)

    hdr = None
    for t, ws in rows:
        toks = [w["text"] for w in ws]
        if len(toks) >= 5 and all(re.fullmatch(r"\d+", x) for x in toks):
            ints = [int(x) for x in toks]
            if ints[0] == 1 and ints[1] == 2 and ints == sorted(ints):
                hdr = (t, ws)
                break
    if hdr is None:
        raise ValueError("column-number row not found")
    hdr_top, hdr_words = hdr
    col_nos = [int(w["text"]) for w in hdr_words][2:]

    parsed = []
    for t, ws in rows:
        if t <= hdr_top + 1:
            continue
        toks = [w["text"] for w in ws]
        i = 0
        if re.fullmatch(r"\d+", toks[0]) and len(toks) > 1 and not NUM_RE.match(toks[1]):
            sl, i = int(toks[0]), 1
        elif toks[0].lower().startswith("state"):
            sl = 0
        else:
            continue
        name_words = []
        while i < len(ws) and not NUM_RE.match(ws[i]["text"]):
            name_words.append(ws[i]["text"])
            i += 1
        if not name_words:
            continue
        nums = [w for w in ws[i:] if NUM_RE.match(w["text"])]
        parsed.append((sl, " ".join(name_words), nums))

    all_x1 = [w["x1"] for _, _, nums in parsed for w in nums]
    centers, spans = _cluster_right_edges(all_x1)
    if len(centers) == len(col_nos) + 1:
        # Printed column-number row may omit exactly one number (seen once: SCR 2024-25 skips "27").
        # Accept only if the omission is a single gap inside an otherwise consecutive range.
        full = list(range(col_nos[0], col_nos[-1] + 1))
        missing = [c for c in full if c not in col_nos]
        if len(missing) == 1 and len(full) == len(centers):
            col_nos = full
            global FIXED_MISSING_COLS
            FIXED_MISSING_COLS.append((missing[0],))
    if len(centers) != len(col_nos):
        raise ValueError(f"{len(centers)} data columns found but {len(col_nos)} printed column numbers")
    spread = max(b - a for a, b in spans)

    out = []
    for sl, name, nums in parsed:
        vals = {}
        for w in nums:
            j = min(range(len(centers)), key=lambda k: abs(w["x1"] - centers[k]))
            if col_nos[j] in vals:
                raise ValueError(f"two values map to col {col_nos[j]} in row {name}")
            vals[col_nos[j]] = float(w["text"])
        out.append({"sl": sl, "district": name, "values": vals})
    return col_nos, out, spread


def find_pages_from_text(pdf_path, regex):
    """0-based page indexes whose pdftotext output (form-feed separated) matches regex in its first lines."""
    import subprocess
    txt = subprocess.run(["pdftotext", "-layout", pdf_path, "-"], capture_output=True, text=True).stdout
    idxs = []
    for i, p in enumerate(txt.split("\f")):
        head = "\n".join(p.strip().split("\n")[:4])
        if regex.search(head):
            idxs.append(i)
    return idxs


def extract_report(pdf_path, regex):
    results = []
    idxs = find_pages_from_text(pdf_path, regex)
    with pdfplumber.open(pdf_path) as pdf:
        for i in idxs:
            page = pdf.pages[i]
            col_nos, rows, worst = parse_table_page(page)
            results.append({"pdf_page": i + 1, "col_nos": col_nos, "rows": rows, "worst_ratio": worst})
            page.flush_cache()
    return results
