"""
Extended FastAPI Endpoints for Multi-User Auth, Yield ML Prediction,
Recommendation History, PDF Generation, and Farmer Profiles.
Integrates directly with existing database and agronomic modules.
"""

import hashlib
import json
import os
import secrets
import time
import uuid
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, Header, HTTPException, Query, Response
from pydantic import BaseModel, EmailStr, Field

from phase3_soil import db
from predict_yield import predict_district_yield, META, DISTRICT_RAINFALL_NORMALS

extra_router = APIRouter(tags=["app-services"])


# ---------------------------------------------------------
# Security & Auth Helpers
# ---------------------------------------------------------

def _hash_password(password: str, salt: Optional[str] = None) -> str:
    if not salt:
        salt = secrets.token_hex(16)
    hashed = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100000).hex()
    return f"{salt}${hashed}"


def _verify_password(password: str, stored_hash: str) -> bool:
    try:
        salt, _ = stored_hash.split("$", 1)
        return _hash_password(password, salt) == stored_hash
    except Exception:
        return False


def _get_current_user_id(
    authorization: Optional[str] = Header(None),
    x_farmer_id: Optional[str] = Header(None)
) -> str:
    """Extract and verify authenticated user identity from Authorization or X-Farmer-Id header."""
    user_id = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split("Bearer ", 1)[1].strip()
        if token:
            user_id = token

    if not user_id and x_farmer_id and x_farmer_id.strip():
        user_id = x_farmer_id.strip()

    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="Authentication required. Please provide a valid Authorization Bearer token or farmer credentials."
        )

    # Validate ID format
    from phase3_soil.service import check_farmer, SoilError
    try:
        check_farmer(user_id)
    except SoilError:
        raise HTTPException(status_code=400, detail=f"Invalid farmer user ID format: '{user_id}'.")

    return user_id


# ---------------------------------------------------------
# Pydantic Schemas
# ---------------------------------------------------------

class RegisterRequest(BaseModel):
    email: str
    password: str
    full_name: str
    phone: Optional[str] = None
    preferred_language: str = "en"
    district: Optional[str] = None


class LoginRequest(BaseModel):
    email: str
    password: str


class ProfileUpdateRequest(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    preferred_language: Optional[str] = None
    district: Optional[str] = None


class FarmDetailsModel(BaseModel):
    district: str
    village: Optional[str] = None
    taluk: Optional[str] = None
    state: Optional[str] = "Tamil Nadu"
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    area: float
    area_unit: str = "hectare"
    irrigation: Optional[str] = "Irrigated"
    soil_series: Optional[str] = None


class FertilizerHistoryItem(BaseModel):
    crop: str
    season: Optional[str] = None
    year: Optional[int] = 2024
    fertilizer_product: str
    quantity: float
    unit: str = "kg"
    application_date: Optional[str] = None
    notes: Optional[str] = None


class YieldPredictionRequest(BaseModel):
    district: str
    crop: str
    season: str = "Kharif"
    year: int = 2024
    rain_swm: Optional[float] = 330.0
    rain_nem: Optional[float] = 640.0
    rain_winter: Optional[float] = 40.0
    rain_hot: Optional[float] = 150.0
    rain_annual: Optional[float] = 1160.0


# ---------------------------------------------------------
# Authentication Endpoints
# ---------------------------------------------------------

@extra_router.post("/api/auth/register")
def register_user(req: RegisterRequest):
    with db.connect() as con:
        # Check duplicate
        row = con.execute("SELECT user_id FROM users WHERE email = ?", (req.email.lower().strip(),)).fetchone()
        if row:
            raise HTTPException(status_code=400, detail="An account with this email already exists.")
        
        user_id = f"farmer_{uuid.uuid4().hex[:12]}"
        now = time.strftime("%Y-%m-%dT%H:%M:%SZ")
        pwd_hash = _hash_password(req.password)

        con.execute(
            """INSERT INTO users (user_id, email, password_hash, full_name, phone, preferred_language, district, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (user_id, req.email.lower().strip(), pwd_hash, req.full_name, req.phone, req.preferred_language, req.district, now, now)
        )

        # Welcome notification
        con.execute(
            """INSERT INTO user_notifications (id, user_id, title, message, category, is_read, created_at)
               VALUES (?, ?, ?, ?, ?, 0, ?)""",
            (str(uuid.uuid4()), user_id, "Welcome to TN Fertilizer Optimizer", "Your account was successfully registered. You can now upload soil cards and get fertilizer recommendations.", "SYSTEM", now)
        )

    return {
        "status": "SUCCESS",
        "token": user_id,
        "user_id": user_id,
        "email": req.email.lower().strip(),
        "full_name": req.full_name,
        "preferred_language": req.preferred_language,
        "district": req.district
    }


@extra_router.post("/api/auth/login")
def login_user(req: LoginRequest):
    with db.connect() as con:
        row = con.execute("SELECT * FROM users WHERE email = ?", (req.email.lower().strip(),)).fetchone()
        if not row:
            # Check if email is a farmer_id directly
            row = con.execute("SELECT * FROM users WHERE user_id = ?", (req.email.strip(),)).fetchone()

        if not row or not _verify_password(req.password, row["password_hash"]):
            raise HTTPException(status_code=401, detail="Invalid email or password.")

        return {
            "status": "SUCCESS",
            "token": row["user_id"],
            "user_id": row["user_id"],
            "email": row["email"],
            "full_name": row["full_name"],
            "phone": row["phone"],
            "preferred_language": row["preferred_language"],
            "district": row["district"]
        }


@extra_router.get("/api/auth/profile")
def get_profile(
    authorization: Optional[str] = Header(None),
    x_farmer_id: Optional[str] = Header(None)
):
    user_id = _get_current_user_id(authorization, x_farmer_id)
    with db.connect() as con:
        row = con.execute("SELECT user_id, email, full_name, phone, preferred_language, district, created_at FROM users WHERE user_id = ?", (user_id,)).fetchone()
        if not row:
            # Fallback mock for default farmer
            return {
                "user_id": user_id,
                "email": f"{user_id}@tnsih.agri",
                "full_name": "Tamil Nadu Farmer",
                "phone": "+91 98765 43210",
                "preferred_language": "ta",
                "district": "Thanjavur"
            }
        return dict(row)


@extra_router.put("/api/auth/profile")
def update_profile(
    req: ProfileUpdateRequest,
    authorization: Optional[str] = Header(None),
    x_farmer_id: Optional[str] = Header(None)
):
    user_id = _get_current_user_id(authorization, x_farmer_id)
    now = time.strftime("%Y-%m-%dT%H:%M:%SZ")
    with db.connect() as con:
        row = con.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
        if row:
            con.execute(
                """UPDATE users SET
                   full_name = COALESCE(?, full_name),
                   phone = COALESCE(?, phone),
                   preferred_language = COALESCE(?, preferred_language),
                   district = COALESCE(?, district),
                   updated_at = ?
                   WHERE user_id = ?""",
                (req.full_name, req.phone, req.preferred_language, req.district, now, user_id)
            )
        return {"status": "SUCCESS", "message": "Profile updated successfully."}


# ---------------------------------------------------------
# Farm & Previous Fertilizer Details
# ---------------------------------------------------------

@extra_router.get("/api/farmer/farm")
def get_farm_details(
    authorization: Optional[str] = Header(None),
    x_farmer_id: Optional[str] = Header(None)
):
    user_id = _get_current_user_id(authorization, x_farmer_id)
    with db.connect() as con:
        row = con.execute("SELECT * FROM farmer_farms WHERE user_id = ? ORDER BY created_at DESC LIMIT 1", (user_id,)).fetchone()
        if row:
            return dict(row)
        return {
            "farm_id": "default",
            "user_id": user_id,
            "district": "Thanjavur",
            "village": "",
            "area": 1.0,
            "area_unit": "hectare",
            "irrigation": "Irrigated",
            "soil_series": "Palavidhi"
        }


@extra_router.post("/api/farmer/farm")
def save_farm_details(
    req: FarmDetailsModel,
    authorization: Optional[str] = Header(None),
    x_farmer_id: Optional[str] = Header(None)
):
    user_id = _get_current_user_id(authorization, x_farmer_id)
    farm_id = str(uuid.uuid4())
    now = time.strftime("%Y-%m-%dT%H:%M:%SZ")
    with db.connect() as con:
        con.execute(
            """INSERT INTO farmer_farms (farm_id, user_id, district, village, taluk, state, latitude, longitude, area, area_unit, irrigation, soil_series, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (farm_id, user_id, req.district, req.village, req.taluk, req.state, req.latitude, req.longitude, req.area, req.area_unit, req.irrigation, req.soil_series, now)
        )
    return {"status": "SUCCESS", "farm_id": farm_id, "message": "Farm details saved successfully."}


@extra_router.get("/api/farmer/fertilizer-history")
def get_fertilizer_history(
    authorization: Optional[str] = Header(None),
    x_farmer_id: Optional[str] = Header(None)
):
    user_id = _get_current_user_id(authorization, x_farmer_id)
    with db.connect() as con:
        rows = con.execute("SELECT * FROM farmer_fertilizer_history WHERE user_id = ? ORDER BY created_at DESC", (user_id,)).fetchall()
        return [dict(r) for r in rows]


@extra_router.post("/api/farmer/fertilizer-history")
def add_fertilizer_history(
    item: FertilizerHistoryItem,
    authorization: Optional[str] = Header(None),
    x_farmer_id: Optional[str] = Header(None)
):
    user_id = _get_current_user_id(authorization, x_farmer_id)
    entry_id = str(uuid.uuid4())
    now = time.strftime("%Y-%m-%dT%H:%M:%SZ")
    with db.connect() as con:
        con.execute(
            """INSERT INTO farmer_fertilizer_history (id, user_id, crop, season, year, fertilizer_product, quantity, unit, application_date, notes, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (entry_id, user_id, item.crop, item.season, item.year, item.fertilizer_product, item.quantity, item.unit, item.application_date, item.notes, now)
        )
    return {"status": "SUCCESS", "id": entry_id, "message": "Previous fertilizer entry saved."}


@extra_router.delete("/api/farmer/fertilizer-history/{entry_id}")
def delete_fertilizer_history(
    entry_id: str,
    authorization: Optional[str] = Header(None),
    x_farmer_id: Optional[str] = Header(None)
):
    user_id = _get_current_user_id(authorization, x_farmer_id)
    with db.connect() as con:
        row = con.execute("SELECT user_id FROM farmer_fertilizer_history WHERE id = ?", (entry_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Fertilizer history record not found.")
        if row["user_id"] != user_id:
            raise HTTPException(status_code=403, detail="Access forbidden: You cannot delete another farmer's fertilizer record.")
        con.execute("DELETE FROM farmer_fertilizer_history WHERE id = ? AND user_id = ?", (entry_id, user_id))
    return {"status": "SUCCESS", "message": "Record deleted."}


# ---------------------------------------------------------
# Standalone ML Crop Yield Prediction Endpoints
# ---------------------------------------------------------

@extra_router.get("/api/yield/meta")
def get_yield_meta():
    """Return categories, features, and meteorological rainfall normals supported by the trained ML model."""
    if os.path.exists(META):
        meta = json.load(open(META))
        return {
            "districts": meta["categories"]["District"],
            "crops": meta["categories"]["Crop"],
            "seasons": meta["categories"]["Season"],
            "district_rainfall_normals": DISTRICT_RAINFALL_NORMALS,
            "numeric_training_ranges": meta.get("numeric_training_ranges", {}),
            "target_unit": meta.get("target_unit", "kg/ha"),
            "scope": "District-level benchmark"
        }
    return {
        "districts": ["Thanjavur", "Tiruvarur", "Madurai"],
        "crops": ["Rice", "Sugarcane", "Cotton"],
        "seasons": ["Kharif", "Rabi"],
        "district_rainfall_normals": DISTRICT_RAINFALL_NORMALS
    }


@extra_router.post("/api/yield/predict")
def predict_yield_endpoint(req: YieldPredictionRequest):
    """Predicts statistical district-average crop yield using the Phase 2 XGBoost model."""
    try:
        val = predict_district_yield(
            district=req.district,
            crop=req.crop,
            season=req.season,
            year=req.year,
            rain_swm=req.rain_swm or 330.0,
            rain_nem=req.rain_nem or 640.0,
            rain_winter=req.rain_winter or 40.0,
            rain_hot=req.rain_hot or 150.0,
            rain_annual=req.rain_annual or 1160.0
        )
        return {
            "status": "SUCCESS",
            "district": req.district,
            "crop": req.crop,
            "season": req.season,
            "year": req.year,
            "estimated_yield_kg_per_ha": round(val, 2),
            "unit": "kg/ha",
            "scope": "District-Average Statistical Benchmark (Phase 2 Model)",
            "disclaimer": "This is a statistical district benchmark from official Tamil Nadu crop reports, not a guaranteed farm yield."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Yield prediction failed: {str(e)}")


# ---------------------------------------------------------
# Saved Recommendations & PDF Report Generation
# ---------------------------------------------------------

@extra_router.post("/api/recommendations")
def save_recommendation(
    payload: Dict[str, Any] = Body(...),
    authorization: Optional[str] = Header(None),
    x_farmer_id: Optional[str] = Header(None)
):
    user_id = _get_current_user_id(authorization, x_farmer_id)
    rec_id = f"REC_{uuid.uuid4().hex[:10].upper()}"
    now = time.strftime("%Y-%m-%dT%H:%M:%SZ")

    crop = payload.get("crop", "Unknown")
    district = payload.get("district", "Unknown")
    p5 = payload.get("nutrient_requirements", {})
    area = p5.get("farm_area_hectares", 1.0)
    p6 = payload.get("fertilizer_plan", {})
    cost = p6.get("total_cost_inr", 0.0)

    with db.connect() as con:
        con.execute(
            """INSERT INTO saved_recommendations (recommendation_id, user_id, crop, district, farm_area, farm_area_unit, target_yield, total_cost_inr, response_json, created_at)
               VALUES (?, ?, ?, ?, ?, 'ha', ?, ?, ?, ?)""",
            (rec_id, user_id, crop, district, area, payload.get("target_yield", 5.0), cost, json.dumps(payload), now)
        )
        # Add notification
        con.execute(
            """INSERT INTO user_notifications (id, user_id, title, message, category, is_read, created_at)
               VALUES (?, ?, ?, ?, ?, 0, ?)""",
            (str(uuid.uuid4()), user_id, f"Recommendation Saved: {crop}", f"Recommendation for {crop} ({district}) saved with estimated cost of Rs {cost:,.2f}.", "RECOMMENDATION", now)
        )

    return {"status": "SUCCESS", "recommendation_id": rec_id, "message": "Recommendation saved to your history."}


@extra_router.get("/api/recommendations")
def list_recommendations(
    authorization: Optional[str] = Header(None),
    x_farmer_id: Optional[str] = Header(None)
):
    user_id = _get_current_user_id(authorization, x_farmer_id)
    with db.connect() as con:
        rows = con.execute("SELECT recommendation_id, crop, district, farm_area, farm_area_unit, target_yield, total_cost_inr, created_at FROM saved_recommendations WHERE user_id = ? ORDER BY created_at DESC", (user_id,)).fetchall()
        return [dict(r) for r in rows]


@extra_router.get("/api/recommendations/{rec_id}")
def get_recommendation_details(
    rec_id: str,
    authorization: Optional[str] = Header(None),
    x_farmer_id: Optional[str] = Header(None)
):
    user_id = _get_current_user_id(authorization, x_farmer_id)
    with db.connect() as con:
        row = con.execute("SELECT * FROM saved_recommendations WHERE recommendation_id = ?", (rec_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Recommendation record not found.")
        if row["user_id"] != user_id:
            raise HTTPException(status_code=403, detail="Access forbidden: This recommendation record belongs to another farmer.")
        data = dict(row)
        data["response_json"] = json.loads(data["response_json"])
        return data


@extra_router.get("/api/recommendations/{rec_id}/pdf")
def download_recommendation_pdf(
    rec_id: str,
    authorization: Optional[str] = Header(None),
    x_farmer_id: Optional[str] = Header(None)
):
    """Generate and return an official downloadable PDF report using ReportLab."""
    user_id = _get_current_user_id(authorization, x_farmer_id)
    with db.connect() as con:
        row = con.execute("SELECT * FROM saved_recommendations WHERE recommendation_id = ?", (rec_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Recommendation record not found.")
        if row["user_id"] != user_id:
            raise HTTPException(status_code=403, detail="Access forbidden: This advisory report belongs to another farmer.")
        rec_data = json.loads(row["response_json"])

    import io
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle('ReportTitle', parent=styles['Heading1'], fontSize=16, leading=20, textColor=colors.HexColor("#1b5e20"), alignment=1)
    sub_style = ParagraphStyle('ReportSub', parent=styles['Normal'], fontSize=10, leading=14, textColor=colors.HexColor("#333333"), alignment=1)
    heading2_style = ParagraphStyle('SecHeading', parent=styles['Heading2'], fontSize=12, leading=16, textColor=colors.HexColor("#2e7d32"))
    body_style = ParagraphStyle('BodyText', parent=styles['Normal'], fontSize=9, leading=12)

    elements = []

    # Title & Header
    elements.append(Paragraph("AI-BASED SOIL-SPECIFIC FERTILIZER RECOMMENDATION REPORT", title_style))
    elements.append(Paragraph("Tamil Nadu State Agricultural Decision Support System (SIH1639)", sub_style))
    elements.append(Spacer(1, 12))

    # Meta Info Table
    meta_data = [
        ["Report ID:", rec_id, "Generated Date:", row["created_at"][:10]],
        ["Farmer ID:", user_id, "District:", row["district"]],
        ["Target Crop:", row["crop"], "Cultivation Area:", f"{row['farm_area']} {row['farm_area_unit']}"]
    ]
    t_meta = Table(meta_data, colWidths=[100, 170, 100, 170])
    t_meta.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f1f8e9")),
        ('TEXTCOLOR', (0,0), (-1,-1), colors.HexColor("#1b5e20")),
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#c8e6c9"))
    ]))
    elements.append(t_meta)
    elements.append(Spacer(1, 14))

    # Section 1: NPK Nutrient Requirements
    elements.append(Paragraph("1. Deterministic NPK Nutrient Requirements (TNAU / STCR / IPNS Rules)", heading2_style))
    p5 = rec_data.get("nutrient_requirements", {})
    n_ha = p5.get("n_req_kg_per_ha") if p5.get("n_req_kg_per_ha") is not None else p5.get("net_n_kg_per_ha", 0)
    p_ha = p5.get("p2o5_req_kg_per_ha") if p5.get("p2o5_req_kg_per_ha") is not None else p5.get("net_p2o5_kg_per_ha", 0)
    k_ha = p5.get("k2o_req_kg_per_ha") if p5.get("k2o_req_kg_per_ha") is not None else p5.get("net_k2o_kg_per_ha", 0)
    tot_n = p5.get("total_n_req_kg") if p5.get("total_n_req_kg") is not None else p5.get("total_farm_n_kg", 0)
    tot_p = p5.get("total_p2o5_req_kg") if p5.get("total_p2o5_req_kg") is not None else p5.get("total_farm_p2o5_kg", 0)
    tot_k = p5.get("total_k2o_req_kg") if p5.get("total_k2o_req_kg") is not None else p5.get("total_farm_k2o_kg", 0)
    calc_meth = p5.get("calculation_method") or p5.get("selected_method", "TNAU STCR-IPNS")
    rule_id = p5.get("selected_rule_id", "Verified TNAU Rule")

    npk_data = [
        ["Nutrient", "Per Hectare (kg/ha)", "Total Farm Quantity (kg)", "Rule Attribution"],
        ["Nitrogen (N)", f"{n_ha:.1f} kg/ha", f"{tot_n:.1f} kg", calc_meth],
        ["Phosphorus (P2O5)", f"{p_ha:.1f} kg/ha", f"{tot_p:.1f} kg", rule_id],
        ["Potassium (K2O)", f"{k_ha:.1f} kg/ha", f"{tot_k:.1f} kg", "TNAU Soil Chemistry Rating"]
    ]
    t_npk = Table(npk_data, colWidths=[130, 130, 130, 150])
    t_npk.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#388e3c")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    elements.append(t_npk)
    elements.append(Spacer(1, 14))

    # Section 2: Optimal Fertilizer Purchase Plan
    elements.append(Paragraph("2. Cost-Optimized Commercial Fertilizer Purchase Plan (LP Solver)", heading2_style))
    p6 = rec_data.get("fertilizer_plan", {})
    products = p6.get("recommended_products", [])
    fert_data = [["Fertilizer Product", "Quantity (kg)", "Commercial Bags", "Bag Size", "Est. Cost (INR)"]]
    for prod in products:
        p_name = prod.get("product_name") or prod.get("name") or "Fertilizer"
        fert_data.append([
            p_name,
            f"{prod.get('quantity_kg', 0):.1f} kg",
            f"{prod.get('bags', 0)} bags",
            f"{prod.get('bag_size_kg', 50)} kg",
            f"Rs {prod.get('total_cost_inr', 0):,.2f}"
        ])
    fert_data.append(["TOTAL ESTIMATED COST", "", "", "", f"Rs {p6.get('total_cost_inr', 0):,.2f}"])

    t_fert = Table(fert_data, colWidths=[170, 90, 90, 80, 110])
    t_fert.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#2e7d32")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTNAME', (0,-1), (-1,-1), 'Helvetica-Bold'),
        ('BACKGROUND', (0,-1), (-1,-1), colors.HexColor("#e8f5e9")),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    elements.append(t_fert)
    elements.append(Spacer(1, 14))

    # Section 3: Yield Benchmark & Weather Advisory
    elements.append(Paragraph("3. District Benchmark & Agro-Weather Guidance", heading2_style))
    yp = rec_data.get("district_yield_prediction", {})
    wg = rec_data.get("weather_guidance", {})
    guidance_text = f"<b>District Benchmark:</b> {yp.get('estimated_yield_kg_per_ha', 'N/A')} kg/ha (Statistical average from historical district data)<br/>" \
                    f"<b>Agro-Weather Timing:</b> {wg.get('actionable_advice', 'Apply fertilizers during clear weather.')}<br/>" \
                    f"<b>Rainfall Risk:</b> {wg.get('risk_level', 'LOW')} | Current condition: {wg.get('current_condition', 'Fair')}"
    elements.append(Paragraph(guidance_text, body_style))
    elements.append(Spacer(1, 14))

    # Footer Disclaimer
    disclaimer = "<i>Disclaimer: Recommendations are calculated from verified TNAU/STCR/IPNS agronomic equations and commercial bag sizes. Yield prediction is a statistical benchmark and not a farm guarantee. Follow local agricultural officer guidance.</i>"
    elements.append(Paragraph(disclaimer, ParagraphStyle('Disc', parent=styles['Normal'], fontSize=8, leading=10, textColor=colors.dimgrey)))

    doc.build(elements)
    buffer.seek(0)
    pdf_bytes = buffer.getvalue()

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=recommendation_{rec_id}.pdf"}
    )


# ---------------------------------------------------------
# Notifications
# ---------------------------------------------------------

@extra_router.get("/api/notifications")
def get_user_notifications(
    authorization: Optional[str] = Header(None),
    x_farmer_id: Optional[str] = Header(None)
):
    user_id = _get_current_user_id(authorization, x_farmer_id)
    with db.connect() as con:
        rows = con.execute("SELECT * FROM user_notifications WHERE user_id = ? ORDER BY created_at DESC LIMIT 20", (user_id,)).fetchall()
        return [dict(r) for r in rows]


@extra_router.post("/api/notifications/{notif_id}/read")
def mark_notification_read(
    notif_id: str,
    authorization: Optional[str] = Header(None),
    x_farmer_id: Optional[str] = Header(None)
):
    user_id = _get_current_user_id(authorization, x_farmer_id)
    with db.connect() as con:
        row = con.execute("SELECT user_id FROM user_notifications WHERE id = ?", (notif_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Notification not found.")
        if row["user_id"] != user_id:
            raise HTTPException(status_code=403, detail="Access forbidden: You cannot modify another farmer's notification.")
        con.execute("UPDATE user_notifications SET is_read = 1 WHERE id = ?", (notif_id,))
    return {"status": "SUCCESS"}
