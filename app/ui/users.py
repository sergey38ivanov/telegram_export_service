from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import User
from app.security import  hash_password, login_required



router = APIRouter()
templates = Jinja2Templates(directory="app/ui/templates")

@router.get("/users", response_class=HTMLResponse)
@login_required
async def users_page(request: Request, db: Session = Depends(get_db)):
    users = db.query(User).all()
    return templates.TemplateResponse("add_user.html", {"request": request, "users": users})

@router.get("/users/add", response_class=HTMLResponse)
def add_user_page(request: Request):
    return templates.TemplateResponse("add_user.html", {"request": request})

@router.post("/users/add")
def add_user(
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    hashed_pw = hash_password(password)
    user = User(username=username, password_hash=hashed_pw)
    db.add(user)
    db.commit()
    return RedirectResponse(url="/users", status_code=303)

