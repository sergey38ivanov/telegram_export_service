from fastapi import APIRouter, BackgroundTasks, Request
from fastapi.responses import StreamingResponse
from app.core.state import CURRENT_CONFIG
from app.core.utils import assign_attributes_from_dict
# from app.core.sync_exporter import run_sync_export  
from app.core.sync_exporter import run_export_in_process
import asyncio
# import aioredis
from redis.asyncio import Redis

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
    print("Поточна конфігурація:", CURRENT_CONFIG)
    assign_attributes_from_dict(CURRENT_CONFIG, data)
    print("Оновлена конфігурація:", CURRENT_CONFIG)
    # asyncio.create_task(perform_export_task("async"))
    return {"status": "Асинхронний експорт запущено"}


@router.post("/execute-sync")
# async def execute_sync(background_tasks: BackgroundTasks):
async def execute_sync(request: Request, background_tasks: BackgroundTasks):
    if not CURRENT_CONFIG:
        return {"error": "Немає конфігурації", "status": "error"}
    print("Запит на синхронний експорт отримано")
    data = await request.json()
    print("Параметри запиту:", data)
    print("Поточна конфігурація:", CURRENT_CONFIG)
    assign_attributes_from_dict(CURRENT_CONFIG, data)
    print("Оновлена конфігурація:", CURRENT_CONFIG)
    # print("BackgroundTasks:", BackgroundTasks)
    # background_tasks.add_task(run_sync_export)
    run_export_in_process(CURRENT_CONFIG)
    return {"status": "Синхронний експорт запущено"}

@router.get("/log-stream")
async def log_stream():
    async def event_generator():
        redis = await Redis.from_url("redis://localhost", decode_responses=True)

        pubsub = redis.pubsub()
        await pubsub.subscribe("log_channel")

        try:
            while True:
                message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                if message and message['type'] == 'message':
                    yield f"data: {message['data']}\n\n"
                await asyncio.sleep(0.1)
        finally:
            await pubsub.unsubscribe("log_channel")
            await pubsub.close()

    return StreamingResponse(event_generator(), media_type="text/event-stream")
