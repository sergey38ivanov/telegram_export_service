import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.routes_config import router as config_router
from app.api.routes_execute import router as execute_router
from app.api.routes_stream import router as stream_router
from app.ui.routes_ui import router as ui_router
from app.db.database import init_db

os.chdir(str(Path(__file__).resolve().parent.parent))

app = FastAPI(title="Telegram Export")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/data", StaticFiles(directory="data"), name="data")
app.mount("/static", StaticFiles(directory="app/ui/static"), name="static")

# Роутери
app.include_router(config_router)
app.include_router(execute_router)
app.include_router(stream_router)
app.include_router(ui_router)

# Ініціалізація бази даних
@app.on_event("startup")
def on_startup():
    init_db()
