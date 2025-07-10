from fastapi import APIRouter, BackgroundTasks, Request
from app.core.state import CURRENT_CONFIG
from app.core.utils import assign_attributes_from_dict
from app.core.sync_exporter import run_sync_export_in_process
import asyncio

router = APIRouter(prefix="/api", tags=["execution"])

async def perform_export_task(mode: str):
    print(f"[{mode.upper()}] ➤ Початок виконання...")
    for i in range(5):
        await asyncio.sleep(1)
        print(f"[{mode.upper()}] Крок {i+1}/5 виконано")
    print(f"[{mode.upper()}] ✔ Завершено")

@router.post("/execute-async")
async def execute_async(request: Request):
    print("Запит на асинхронний експорт отримано")
    if not CURRENT_CONFIG:
        return {"error": "Немає конфігурації", "status": "error"}
    data = await request.json()
    print("Параметри запиту:", data)
    assign_attributes_from_dict(CURRENT_CONFIG, data)
    return {"status": "Асинхронний експорт запущено"}


@router.post("/execute-sync")
async def execute_sync(request: Request, background_tasks: BackgroundTasks):
    if not CURRENT_CONFIG:
        return {"error": "Немає конфігурації", "status": "error"}
    print("Запит на синхронний експорт отримано")
    data = await request.json()
    print("Параметри запиту:", data)
    assign_attributes_from_dict(CURRENT_CONFIG, data)
    run_sync_export_in_process(CURRENT_CONFIG)
    return {"status": "Синхронний експорт запущено"}

