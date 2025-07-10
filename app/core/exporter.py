from pyrogram import Client
from app.core.state import ExportConfig
from app.config import settings
import asyncio
import json
from pathlib import Path
from datetime import datetime
from typing import Callable

EXPORT_DIR = Path("exports")
EXPORT_DIR.mkdir(exist_ok=True)


async def export_data(config: ExportConfig, sse_callback: Callable[[str], asyncio.Future] = None):
    """
    Основна функція експорту: підключення до Telegram, експорт чатів за config,
    опціональне повідомлення через SSE.
    """
    export_id = datetime.now(datetime.timezone.utc).strftime("%Y%m%d_%H%M%S")
    output_file = EXPORT_DIR / f"export_{export_id}.json"
    
    async with Client(
        name="tg_export",
        session_string=config.session_string,
        api_id=settings.API_ID,
        api_hash=settings.API_HASH
    ) as app:

        result = []
        async for dialog in app.get_dialogs():
            if config.chat_ids and str(dialog.chat.id) not in config.chat_ids:
                continue

            chat_info = {
                "chat_id": dialog.chat.id,
                "title": dialog.chat.title or "private",
                "type": dialog.chat.type,
                "messages": []
            }

            async for message in app.get_chat_history(dialog.chat.id, limit=config.messages_limit):
                msg_data = {
                    "id": message.id,
                    "date": str(message.date),
                    "text": message.text or "",
                    "from_user": message.from_user.first_name if message.from_user else None
                }
                chat_info["messages"].append(msg_data)

            result.append(chat_info)

            if sse_callback:
                await sse_callback(f"Опрацьовано чат {dialog.chat.id} ({dialog.chat.title})")

        # Зберігаємо результат
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        if sse_callback:
            await sse_callback(f"Експорт завершено. Збережено у {output_file.name}")

        return output_file.name