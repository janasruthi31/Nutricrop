"""FastAPI router for Phase 3. Mount into the existing app with:  app.include_router(soil_router)"""
import hmac
from typing import Optional

from fastapi import APIRouter, Body, File, Header, UploadFile
from fastapi.responses import JSONResponse

from . import config, service
from .service import SoilError

soil_router = APIRouter(prefix="/api/soil", tags=["phase3-soil"])


def _guard(x_farmer_id, x_api_key):
    """Placeholder auth: replace with the app's real authentication when it exists."""
    if config.API_KEY and not (x_api_key and hmac.compare_digest(x_api_key, config.API_KEY)):
        raise SoilError("UNAUTHORIZED", "Invalid or missing API key.", 401)
    return service.check_farmer(x_farmer_id)


def _err(e: SoilError):
    return JSONResponse(status_code=e.http_status, content=e.to_dict())


@soil_router.post("/upload")
def upload_report(file: UploadFile = File(...), x_farmer_id: str = Header(None), x_api_key: Optional[str] = Header(None)):
    try:
        farmer = _guard(x_farmer_id, x_api_key)
        data = file.file.read(config.MAX_UPLOAD_BYTES + 1)  # bounded read: never loads an unbounded body
        return service.upload(farmer, data)
    except SoilError as e:
        return _err(e)
    except Exception:
        return _err(SoilError("SERVER_ERROR", "Something went wrong on the server. Please try again.", 500))


@soil_router.post("/ocr")
def ocr_report(body: dict = Body(...), x_farmer_id: str = Header(None), x_api_key: Optional[str] = Header(None)):
    try:
        farmer = _guard(x_farmer_id, x_api_key)
        return service.run_ocr(farmer, str(body.get("document_id", "")))
    except SoilError as e:
        return _err(e)
    except Exception:
        return _err(SoilError("SERVER_ERROR", "Something went wrong on the server. Please try again.", 500))


@soil_router.post("/validate")
def validate_values(body: dict = Body(...), x_farmer_id: str = Header(None), x_api_key: Optional[str] = Header(None)):
    try:
        _guard(x_farmer_id, x_api_key)
        return service.validate(body)
    except SoilError as e:
        return _err(e)
    except Exception:
        return _err(SoilError("SERVER_ERROR", "Something went wrong on the server. Please try again.", 500))


@soil_router.post("/confirm")
def confirm_values(body: dict = Body(...), x_farmer_id: str = Header(None), x_api_key: Optional[str] = Header(None)):
    try:
        farmer = _guard(x_farmer_id, x_api_key)
        return service.confirm(farmer, body)
    except SoilError as e:
        return _err(e)
    except Exception:
        return _err(SoilError("SERVER_ERROR", "Something went wrong on the server. Please try again.", 500))


@soil_router.get("/{soil_profile_id}")
def get_soil_profile(soil_profile_id: str, x_farmer_id: str = Header(None), x_api_key: Optional[str] = Header(None)):
    try:
        farmer = _guard(x_farmer_id, x_api_key)
        return service.get_profile(farmer, soil_profile_id)
    except SoilError as e:
        return _err(e)
    except Exception:
        return _err(SoilError("SERVER_ERROR", "Something went wrong on the server. Please try again.", 500))
