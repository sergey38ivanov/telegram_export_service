from passlib.context import CryptContext
from datetime import datetime, timedelta
from jose import JWTError, jwt
import hashlib
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.responses import RedirectResponse
from functools import wraps

SECRET_KEY = "supersecretkey"  # ⚠️ заміни на .env
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    if len(password.encode("utf-8")) > 72:
        # попередньо стискаємо пароль у SHA256
        password = hashlib.sha256(password.encode("utf-8")).hexdigest()
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    if len(plain_password.encode("utf-8")) > 72:
        plain_password = hashlib.sha256(plain_password.encode("utf-8")).hexdigest()
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

security = HTTPBasic()

# Фейкова функція для перевірки юзера
def get_current_user(credentials: HTTPBasicCredentials = Depends(security)):
    # Тут можна підключити вашу базу та перевірку пароля
    if credentials.username != "admin" or credentials.password != "secret":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username

def login_required(func):
    @wraps(func)
    async def wrapper(request: Request, *args, **kwargs):
        if "user" not in request.session:
            return RedirectResponse("/login", status_code=303)
        return await func(request, *args, **kwargs)
    return wrapper