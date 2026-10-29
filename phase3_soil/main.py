import html
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse

from . import db
from .api import soil_router
from agronomy.api import agronomy_router
from phase5_nutrient.api import nutrient_router
import os
import hmac
from phase6_fertilizer.api import fertilizer_router, fertilizer_opt_router
from phase7_integration.api import integration_router
from phase7_integration.extra_api import extra_router
from typing import Optional, Set
from fastapi import Header, HTTPException

app = FastAPI(title="Sustainable Fertilizer Usage Optimizer Master API (Phases 1-8)")

# Security: Enable CORS with configurable origins from environment
allowed_origins_env = os.environ.get("ALLOWED_ORIGINS", "*")
allowed_origins = [o.strip() for o in allowed_origins_env.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins if allowed_origins else ["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

db.init_db()
app.include_router(soil_router)
app.include_router(agronomy_router)
app.include_router(nutrient_router)
app.include_router(fertilizer_router)
app.include_router(fertilizer_opt_router)
app.include_router(integration_router)
app.include_router(extra_router)

ADMIN_API_KEY = os.environ.get("ADMIN_API_KEY")
if not ADMIN_API_KEY:
    if os.environ.get("ENVIRONMENT", "").lower() == "production":
        raise RuntimeError("FATAL: ADMIN_API_KEY environment variable must be set in production mode!")
    ADMIN_API_KEY = "tnau_agri_admin_secret_key_2026"
ENABLE_ADMIN_DIAGNOSTICS = os.environ.get("ENABLE_ADMIN_DIAGNOSTICS", "false").lower() in ("true", "1")
ALLOWED_DIAGNOSTIC_TABLES = {
    "soil_profiles", "soil_profile_fields", "farmer_farms", 
    "farmer_fertilizer_history", "saved_recommendations", "weather_cache", "fertilizer_prices"
}


@app.get("/")
def root():
    return {
        "status": "online",
        "system": "AI-Based Soil-Specific Fertilizer Recommendation & Crop Yield Prediction System for Tamil Nadu Farmers",
        "version": "1.0.0",
        "docs_url": "/docs",
        "health_url": "/health"
    }


@app.get("/health")
def health():
    try:
        with db.connect() as con:
            cur = con.cursor()
            cur.execute("SELECT COUNT(*) FROM soil_profiles")
            profiles_cnt = cur.fetchone()[0]
        return {
            "status": "ok",
            "database": "sqlite3",
            "database_connected": True,
            "profiles_saved": profiles_cnt
        }
    except Exception as e:
        return {"status": "ok", "database": "sqlite3", "database_connected": False, "error": str(e)}


@app.get("/download-apk")
def download_apk():
    apk_path = "flutter_app/build/app/outputs/flutter-apk/app-release.apk"
    if not os.path.exists(apk_path):
        raise HTTPException(
            status_code=404,
            detail="Release APK is not yet compiled. Run 'flutter build apk --release' in flutter_app/ to generate it."
        )
    return FileResponse(apk_path, media_type="application/vnd.android.package-archive", filename="app-release.apk")


def _verify_admin_access(x_admin_key: Optional[str] = None):
    """Enforces strict administrative authorization for diagnostics."""
    if not ENABLE_ADMIN_DIAGNOSTICS:
        raise HTTPException(
            status_code=403, 
            detail="Administrative database diagnostics are disabled in this environment."
        )
    if not x_admin_key or not hmac.compare_digest(x_admin_key, ADMIN_API_KEY):
        raise HTTPException(
            status_code=401, 
            detail="Unauthorized: Valid X-Admin-Key header required to access database diagnostics."
        )


@app.get("/api/db/status")
def db_status(x_admin_key: Optional[str] = Header(None)):
    """Inspect SQLite database connectivity and record counts. Restricted to authorized administrators."""
    _verify_admin_access(x_admin_key)
    try:
        with db.connect() as con:
            cur = con.cursor()
            cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
            tables = {}
            for r in cur.fetchall():
                tbl = r["name"]
                if tbl in ALLOWED_DIAGNOSTIC_TABLES:
                    c = con.execute(f"SELECT COUNT(*) FROM {tbl}").fetchone()[0]
                    tables[tbl] = c
        return {
            "status": "connected",
            "database_type": "SQLite3",
            "database_path": db.config.DB_PATH,
            "total_tables": len(tables),
            "tables": tables
        }
    except Exception as e:
        return {
            "status": "error",
            "database_type": "SQLite3",
            "error": str(e)
        }


@app.get("/db", response_class=HTMLResponse)
def view_db_dashboard(table: str = Query("soil_profiles"), x_admin_key: Optional[str] = Header(None)):
    """Visual SQLite Database Dashboard for authorized administrators."""
    _verify_admin_access(x_admin_key)
    if table not in ALLOWED_DIAGNOSTIC_TABLES:
        raise HTTPException(status_code=400, detail=f"Access to table '{table}' is restricted or not in diagnostic allowlist.")
    try:
        with db.connect() as con:
            cur = con.cursor()
            cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
            all_tables = [r["name"] for r in cur.fetchall() if r["name"] in ALLOWED_DIAGNOSTIC_TABLES]
            if not all_tables:
                return "<h3>No diagnostic tables available.</h3>"
            if table not in all_tables:
                table = all_tables[0]

            counts = {}
            for t in all_tables:
                counts[t] = con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]

            cur.execute(f"SELECT * FROM {table} LIMIT 250")
            rows = cur.fetchall()
            cols = [d[0] for d in cur.description] if cur.description else []

            tabs_html = ""
            for t in all_tables:
                active_class = "active" if t == table else ""
                badge = f'<span class="badge">{counts[t]}</span>'
                tabs_html += f'<a href="/db?table={t}" class="tab-btn {active_class}">{t} {badge}</a>'

            headers_html = "".join(f"<th>{html.escape(c)}</th>" for c in cols)
            rows_html = ""
            for r in rows:
                cells = ""
                for c in cols:
                    val = r[c]
                    val_str = "" if val is None else str(val)
                    if len(val_str) > 120 and (val_str.startswith("{") or val_str.startswith("[")):
                        cells += f'<td><div class="code-box">{html.escape(val_str)}</div></td>'
                    else:
                        cells += f'<td>{html.escape(val_str)}</td>'
                rows_html += f"<tr>{cells}</tr>"

            if not rows:
                rows_html = f'<tr><td colspan="{len(cols) or 1}" style="text-align:center; padding: 24px; color: #777;">No records found in table <b>{table}</b></td></tr>'

            return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>TN Fertilizer Optimizer - SQLite Database Visualizer</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
      background-color: #f8fafc;
      color: #1e293b;
      padding: 24px;
    }}
    .header {{
      background: white;
      border-radius: 12px;
      padding: 20px 24px;
      box-shadow: 0 1px 3px rgba(0,0,0,0.08);
      margin-bottom: 20px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 12px;
    }}
    .header h1 {{
      font-size: 20px;
      color: #1b5e20;
      display: flex;
      align-items: center;
      gap: 8px;
    }}
    .db-path {{
      font-size: 13px;
      color: #64748b;
      font-family: monospace;
      background: #f1f5f9;
      padding: 6px 10px;
      border-radius: 6px;
    }}
    .status-badge {{
      background: #e8f5e9;
      color: #2e7d32;
      padding: 6px 12px;
      border-radius: 20px;
      font-weight: 600;
      font-size: 12px;
      display: inline-flex;
      align-items: center;
      gap: 6px;
    }}
    .tabs-bar {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-bottom: 20px;
    }}
    .tab-btn {{
      background: white;
      text-decoration: none;
      color: #475569;
      padding: 8px 14px;
      border-radius: 8px;
      font-size: 13px;
      font-weight: 500;
      box-shadow: 0 1px 2px rgba(0,0,0,0.05);
      border: 1px solid #e2e8f0;
      display: flex;
      align-items: center;
      gap: 6px;
      transition: all 0.15s ease;
    }}
    .tab-btn:hover {{
      border-color: #2e7d32;
      color: #2e7d32;
    }}
    .tab-btn.active {{
      background: #2e7d32;
      color: white;
      border-color: #2e7d32;
      box-shadow: 0 2px 6px rgba(46,125,50,0.3);
    }}
    .tab-btn.active .badge {{
      background: rgba(255,255,255,0.25);
      color: white;
    }}
    .badge {{
      background: #f1f5f9;
      color: #475569;
      font-size: 11px;
      padding: 2px 6px;
      border-radius: 10px;
      font-weight: 600;
    }}
    .table-container {{
      background: white;
      border-radius: 12px;
      box-shadow: 0 1px 3px rgba(0,0,0,0.08);
      overflow: hidden;
      border: 1px solid #e2e8f0;
    }}
    .table-toolbar {{
      padding: 14px 20px;
      border-bottom: 1px solid #e2e8f0;
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 12px;
    }}
    .table-title {{
      font-size: 16px;
      font-weight: 600;
      color: #0f172a;
    }}
    .search-input {{
      padding: 7px 12px;
      border: 1px solid #cbd5e1;
      border-radius: 6px;
      font-size: 13px;
      width: 260px;
      outline: none;
    }}
    .search-input:focus {{
      border-color: #2e7d32;
    }}
    .table-scroll {{
      overflow-x: auto;
      max-height: 720px;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 13px;
    }}
    th {{
      background: #f8fafc;
      color: #475569;
      font-weight: 600;
      text-align: left;
      padding: 10px 14px;
      border-bottom: 1px solid #e2e8f0;
      position: sticky;
      top: 0;
      z-index: 10;
      white-space: nowrap;
    }}
    td {{
      padding: 10px 14px;
      border-bottom: 1px solid #f1f5f9;
      color: #334155;
      vertical-align: top;
      max-width: 450px;
      word-break: break-word;
    }}
    tr:hover td {{
      background-color: #f8fafc;
    }}
    .code-box {{
      font-family: monospace;
      font-size: 11px;
      max-height: 80px;
      overflow-y: auto;
      background: #f8fafc;
      padding: 6px;
      border-radius: 4px;
      border: 1px solid #e2e8f0;
    }}
  </style>
</head>
<body>
  <div class="header">
    <div>
      <h1>🌱 TN Fertilizer Optimizer — SQLite Database Visualizer</h1>
      <div style="margin-top: 6px;">
        <span class="db-path">File: {db.config.DB_PATH}</span>
      </div>
    </div>
    <div style="display: flex; gap: 10px; align-items: center;">
      <span class="status-badge">● SQLite Connected</span>
      <a href="/db?table={table}" style="font-size: 13px; color: #2e7d32; text-decoration: none; font-weight: 600; border: 1px solid #c8e6c9; padding: 6px 12px; border-radius: 6px; background: white;">⟳ Refresh</a>
    </div>
  </div>

  <div class="tabs-bar">
    {tabs_html}
  </div>

  <div class="table-container">
    <div class="table-toolbar">
      <div class="table-title">Table: <b>{table}</b> ({len(rows)} shown of {counts[table]} total)</div>
      <input type="text" id="filterInput" class="search-input" placeholder="Filter rows in this table..." onkeyup="filterRows()">
    </div>
    <div class="table-scroll">
      <table id="dataTable">
        <thead>
          <tr>{headers_html}</tr>
        </thead>
        <tbody>
          {rows_html}
        </tbody>
      </table>
    </div>
  </div>

  <script>
    function filterRows() {{
      const query = document.getElementById('filterInput').value.toLowerCase();
      const rows = document.querySelectorAll('#dataTable tbody tr');
      rows.forEach(r => {{
        const text = r.textContent.toLowerCase();
        r.style.display = text.includes(query) ? '' : 'none';
      }});
    }}
  </script>
</body>
</html>"""
    except Exception as e:
        return f"<h3>Database inspection error: {html.escape(str(e))}</h3>"

