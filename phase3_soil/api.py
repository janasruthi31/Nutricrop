"""FastAPI router for Phase 3. Mount into the existing app with:  app.include_router(soil_router)"""
import hmac
from typing import Optional

from fastapi import APIRouter, Body, File, Header, UploadFile
from fastapi.responses import JSONResponse

from . import config, service
from .service import SoilError

soil_router = APIRouter(prefix="/api/soil", tags=["phase3-soil"])


def _guard(x_farmer_id: Optional[str], x_api_key: Optional[str], authorization: Optional[str] = None):
    """Checks API key and extracts farmer identity securely from verified JWT or controlled test harness."""
    import os
    if config.API_KEY and not (x_api_key and hmac.compare_digest(x_api_key, config.API_KEY)):
        raise SoilError("UNAUTHORIZED", "Invalid or missing API key.", 401)

    token = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split("Bearer ", 1)[1].strip()

    if token:
        if token.count(".") == 2:
            from phase7_integration.extra_api import _verify_jwt_token
            payload = _verify_jwt_token(token)
            if not payload or not payload.get("sub"):
                raise SoilError("UNAUTHORIZED", "Invalid or expired authentication token. Please log in again.", 401)
            return service.check_farmer(payload["sub"])
        elif os.environ.get("AGRI_ALLOW_TEST_BYPASS", "false").lower() in ("true", "1"):
            return service.check_farmer(token)
        else:
            raise SoilError("UNAUTHORIZED", "Invalid authentication token format. A valid signed JWT is required.", 401)

    if x_farmer_id:
        if os.environ.get("AGRI_ALLOW_TEST_BYPASS", "false").lower() in ("true", "1") and (x_farmer_id.startswith("test_farmer_") or x_farmer_id.startswith("farmer_")):
            return service.check_farmer(x_farmer_id)
        raise SoilError("UNAUTHORIZED", "Authentication required. X-Farmer-Id header is not accepted as proof of authentication.", 401)

    raise SoilError("UNAUTHORIZED", "Authentication required. Please provide a valid Authorization Bearer token.", 401)


def _err(e: SoilError):
    return JSONResponse(status_code=e.http_status, content=e.to_dict())


@soil_router.post("/upload")
def upload_report(
    file: UploadFile = File(...),
    x_farmer_id: Optional[str] = Header(None),
    x_api_key: Optional[str] = Header(None),
    authorization: Optional[str] = Header(None)
):
    try:
        farmer = _guard(x_farmer_id, x_api_key, authorization)
        data = file.file.read(config.MAX_UPLOAD_BYTES + 1)  # bounded read: never loads an unbounded body
        return service.upload(farmer, data)
    except SoilError as e:
        return _err(e)
    except Exception:
        return _err(SoilError("SERVER_ERROR", "Something went wrong on the server. Please try again.", 500))


@soil_router.post("/ocr")
def ocr_report(
    body: dict = Body(...),
    x_farmer_id: Optional[str] = Header(None),
    x_api_key: Optional[str] = Header(None),
    authorization: Optional[str] = Header(None)
):
    try:
        farmer = _guard(x_farmer_id, x_api_key, authorization)
        return service.run_ocr(farmer, str(body.get("document_id", "")))
    except SoilError as e:
        return _err(e)
    except Exception:
        return _err(SoilError("SERVER_ERROR", "Something went wrong on the server. Please try again.", 500))


@soil_router.post("/validate")
def validate_values(
    body: dict = Body(...),
    x_farmer_id: Optional[str] = Header(None),
    x_api_key: Optional[str] = Header(None),
    authorization: Optional[str] = Header(None)
):
    try:
        _guard(x_farmer_id, x_api_key, authorization)
        return service.validate(body)
    except SoilError as e:
        return _err(e)
    except Exception:
        return _err(SoilError("SERVER_ERROR", "Something went wrong on the server. Please try again.", 500))


@soil_router.post("/confirm")
def confirm_values(
    body: dict = Body(...),
    x_farmer_id: Optional[str] = Header(None),
    x_api_key: Optional[str] = Header(None),
    authorization: Optional[str] = Header(None)
):
    try:
        farmer = _guard(x_farmer_id, x_api_key, authorization)
        return service.confirm(farmer, body)
    except SoilError as e:
        return _err(e)
    except Exception:
        return _err(SoilError("SERVER_ERROR", "Something went wrong on the server. Please try again.", 500))


@soil_router.get("/{soil_profile_id}")
def get_soil_profile(
    soil_profile_id: str,
    x_farmer_id: Optional[str] = Header(None),
    x_api_key: Optional[str] = Header(None),
    authorization: Optional[str] = Header(None)
):
    try:
        farmer = _guard(x_farmer_id, x_api_key, authorization)
        return service.get_profile(farmer, soil_profile_id)
    except SoilError as e:
        return _err(e)
    except Exception:
        return _err(SoilError("SERVER_ERROR", "Something went wrong on the server. Please try again.", 500))
