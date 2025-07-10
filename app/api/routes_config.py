from fastapi import APIRouter
from app.core.state import ExportConfig, CURRENT_CONFIG

router = APIRouter(prefix="/api/config", tags=["config"])

@router.post("/")
async def set_config(config: ExportConfig):
    global CURRENT_CONFIG
    CURRENT_CONFIG = config
    return {"status": "ok"}

@router.get("/")
async def get_config():
    return CURRENT_CONFIG