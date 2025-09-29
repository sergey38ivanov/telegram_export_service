from fastapi import FastAPI, HTTPException, Request, Depends, Form, APIRouter
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from sqlalchemy.orm import Session
from app.db.database import SessionLocal, engine
from app.db.models import Base, TelegramChannel, RedirectLink, Domain, generate_key, Sessions
from app.config import settings
from starlette.templating import Jinja2Templates


Base.metadata.create_all(bind=engine)

router = APIRouter(prefix="/configuration", tags=["configuration"])
templates = Jinja2Templates(directory="app/ui/templates")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/", response_class=HTMLResponse)
async def index(request: Request, db: Session = Depends(get_db)):
    channels = db.query(TelegramChannel).all()
    domains = db.query(Domain).all()
    redirects = db.query(RedirectLink).all()
    sessions = db.query(Sessions).all()

    return templates.TemplateResponse("configurations.html", 
                                      {"request": request, 
                                       "channels": channels, 
                                       "domains": domains,
                                       "redirects": redirects,
                                       "sessions": sessions})


@router.post("/add_channel")
async def add_channel(data: dict, db: Session = Depends(get_db)):
    channel = TelegramChannel(
        photo=data.get("photo"),
        name=data.get("name"),
        invite_link=data.get("invite_link")
    )
    db.add(channel)
    db.commit()
    db.refresh(channel)
    return {"status": "ok", "channel_id": channel.id}


@router.post("/add_redirect")
async def add_redirect(data: dict, db: Session = Depends(get_db)):
    key = generate_key()
    domain_id = data.get("domain_id")
    domain = db.query(Domain).filter(Domain.id == domain_id).first()
    if not domain:
        return JSONResponse({"status": "error", "message": "Domain not found"}, status_code=400)

    # full_link = f"https://{domain.domen}/{key}"
    full_link = f"http://{domain.domen}/{key}"

    redirect = RedirectLink(
        id=key,
        link=full_link,
        redirect_id=data.get("redirect_id"),
        phone=data.get("phone"),
    )
    db.add(redirect)
    db.commit()
    db.refresh(redirect)
    return {"status": "ok", "link": redirect.link}


@router.post("/add_domain")
async def add_domain(data: dict, db: Session = Depends(get_db)):
    domain = Domain(
        name=data.get("name"),
        domen=data.get("domen")
    )
    db.add(domain)
    db.commit()
    db.refresh(domain)
    return {"status": "ok", "domain_id": domain.id}


@router.delete("/redirects/{recordId}")
async def delete_channel(recordId: str, db: Session = Depends(get_db)):
    record = db.query(RedirectLink).filter(RedirectLink.id == recordId).first()
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    
    db.delete(record)
    db.commit()
    return {"status": "success", "message": f"Channel {recordId} deleted"}