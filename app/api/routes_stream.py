from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
import asyncio

router = APIRouter()

async def event_generator():
    for i in range(1, 6):
        yield f"data: {{\"progress\": {i * 20}}}\n\n"
        await asyncio.sleep(1)
    yield f"data: {{\"status\": \"complete\"}}\n\n"

@router.get("/stream")
async def stream(request: Request):
    return StreamingResponse(event_generator(), media_type="text/event-stream")
