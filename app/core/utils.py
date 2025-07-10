#  File: telegram_export_service/app/core/utils.py

from pydantic import BaseModel

def assign_attributes_from_dict(obj: BaseModel, data: dict):
    """
    Оновлює атрибути об'єкта Pydantic-моделі з переданого словника.
    Ігнорує ключі, яких немає у моделі.
    """
    for key, value in data.items():
        if key in obj.model_fields:
            # Перевіряємо, чи значення не None
            if key == "chat_ids" and value is None:
                setattr(obj, key, [])
                continue
            setattr(obj, key, value)
        else:
            print(f"⚠️ Поле '{key}' не визначене у {obj.__class__.__name__}, пропущено.")

# -------------------------------------------------------------------------------------------

import redis

# Підключення до Redis (можна винести в конфіг)
redis_client = redis.Redis(host='localhost', port=6379, db=0)

CHANNEL = "log_channel"

def sse_log(message: str):
    redis_client.publish(CHANNEL, message)
