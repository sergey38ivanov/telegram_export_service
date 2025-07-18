import json
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, Request, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.config import settings
from sqlalchemy.orm import Session
from app.db.models import ExportRecord
from app.db.database import SessionLocal


router = APIRouter()
templates = Jinja2Templates(directory="app/ui/templates")

@router.get("/export", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@router.get("/view-export")
async def view_export(request: Request, id: Optional[str] = Query(default=None)):

    data_path = settings.BASE_DIR / "data"
    folders = [
        f.name for f in data_path.iterdir()
        if f.is_dir() and not f.name.startswith(".")
    ]
    print("selected_folder", id)
    
    if id:
        db_record = get_export_record_by_id(SessionLocal(), int(id))
        selected_folder = db_record.directory_name if db_record else None
    else:
        selected_folder = None
    return templates.TemplateResponse("export_view.html", {
        "request": request,
        "folders": folders,
        "selected_folder": selected_folder,
    })

def get_export_record_by_id(session: Session, id: int):
    return session.get(ExportRecord, id)