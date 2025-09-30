from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models import User
from app.security import  verify_password, create_access_token

router = APIRouter()
templates = Jinja2Templates(directory="app/ui/templates")

@router.get("/login", response_class=HTMLResponse)
def login_form(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@router.post("/login")
async def login(request: Request, 
                username: str = Form(...), 
                password: str = Form(...), 
                db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == username).first()
    if not user or not verify_password(password, user.password_hash):
        # Неуспішна авторизація
        return RedirectResponse("/login", status_code=303)

    # Успішна авторизація — зберігаємо в сесії
    request.session["user"] = user.username
    return RedirectResponse("/sessions", status_code=303)

@router.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login", status_code=303)