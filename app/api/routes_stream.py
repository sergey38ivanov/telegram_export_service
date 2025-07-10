from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
import asyncio
from redis.asyncio import Redis

router = APIRouter()

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