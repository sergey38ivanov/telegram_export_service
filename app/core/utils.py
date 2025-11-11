#  File: telegram_export_service/app/core/utils.py

from pydantic import BaseModel

def assign_attributes_from_dict(obj: BaseModel, data: dict):
    """
    Оновлює атрибути об'єкта Pydantic-моделі з переданого словника.
    Ігнорує ключі, яких немає у моделі.
    """
    if "chat_ids" not in data:
        setattr(obj, "chat_ids", [])
    for key, value in data.items():
        if key in obj.model_fields:
            # Перевіряємо, чи значення не None
            if key == "chat_ids" and value is None:
                setattr(obj, key, [])
                continue
            try:
                setattr(obj, key, value)
            except Exception as e:
                print(f"❌ Не вдалося призначити {key}: {e}")
        else:
            print(f"⚠️ Поле '{key}' не визначене у {obj.__class__.__name__}, пропущено.")

# -------------------------------------------------------------------------------------------

import redis

# Підключення до Redis (можна винести в конфіг)
redis_client = redis.Redis(host='localhost', port=6379, db=0)

CHANNEL = "log_channel"

def sse_log(message: str):
    redis_client.publish(CHANNEL, message)

# -------------------------------------------------------------------------------------------

from datetime import datetime

def generate_directory_name(phone: str, name: str, export_date: datetime) -> str:
    timestamp = export_date.strftime("%d%m%Y%H%M%S")
    return f"{phone}__{name}_{timestamp}"

