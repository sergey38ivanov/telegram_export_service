from fastapi import APIRouter, BackgroundTasks, Request
from fastapi.responses import JSONResponse
from app.core.state import CURRENT_CONFIG
from app.core.utils import assign_attributes_from_dict
from app.core.sync_exporter import run_sync_export_in_process
import asyncio
from sqlalchemy.orm import Session
from app.db.models import ExportRecord
from app.db.database import SessionLocal
from app.core.teletopyrostring import tele_to_pyro
from app.core.gramjstopyro import gramjs_to_pyro

router = APIRouter(prefix="/api", tags=["execution"])


@router.post("/execute-async")
async def execute_async(request: Request):
    print("Asynchronous export request received")
    if not CURRENT_CONFIG:
        return {"error": "No configuration", "status": "error"}
    data = await request.json()
    print("Параметри запиту:", data)
    assign_attributes_from_dict(CURRENT_CONFIG, data)
    return {"status": "Asynchronous export started"}


@router.post("/execute-sync")
async def execute_sync(request: Request, background_tasks: BackgroundTasks):
    # try:
    if True:
        print("Synchronous export request received")
        data = await request.json()
        print("Параметри запиту:", data)
        
        print(1)
        if not CURRENT_CONFIG or not data:
            return {"error": "No configuration", "status": "error"}
        if "session_string" not in data:
            return {"error": "Missing 'Session data'", "status": "error"}
        elif data["session_string"] == {}:
            return {"error": "Missing 'Session data'", "status": "error"}
        print(2)
        if data["session_string"]["session_type"] == "gramjs":
            print(21)
            data["session_string"] = await gramjs_to_pyro(data["session_string"], CURRENT_CONFIG.api_id, CURRENT_CONFIG.api_hash)
        elif data["session_string"]["session_type"] == "telethon":
            print(22)
            data["session_string"] = await tele_to_pyro(data["session_string"], CURRENT_CONFIG.api_id, CURRENT_CONFIG.api_hash)
        elif  data["session_string"]["session_type"] == "pyrogram":
            data["session_string"] = data["session_string"]["auth_key"]
        
        print(3)
        assign_attributes_from_dict(CURRENT_CONFIG, data)
        print("assigned")
        run_sync_export_in_process(CURRENT_CONFIG)
        export_id = get_last_entry_id(SessionLocal()) + 1
        print(export_id)
        return {"status": "Synchronous export started", "export_id": export_id}

    # except Exception as e:
    #     print(f"[ERROR] Помилка в execute-sync: {e}")
    #     return JSONResponse(
    #         status_code=500,
    #         content={
    #             "status": "error",
    #             "error": str(e),
    #         }
    #     )

def get_last_entry_id(db: Session) -> int:
    last_entry = db.query(ExportRecord).order_by(ExportRecord.id.desc()).first()
    return last_entry.id if last_entry else 0

