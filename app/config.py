import json
from typing import List, Optional, ClassVar
from pydantic import validator, field_validator
from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    API_ID: int
    API_HASH: str
    SESSION_STRING: Optional[str] = None

    CHAT_IDS: List[str] = []

    MEDIA_EXPORT_AUDIOS: bool = False
    MEDIA_EXPORT_VIDEOS: bool = False
    MEDIA_EXPORT_PHOTOS: bool = True
    MEDIA_EXPORT_STICKERS: bool = False
    MEDIA_EXPORT_ANIMATIONS: bool = False
    MEDIA_EXPORT_DOCUMENTS: bool = True
    MEDIA_EXPORT_VOICE_MESSAGES: bool = False
    MEDIA_EXPORT_VIDEO_MESSAGES: bool = False
    MEDIA_EXPORT_CONTACTS: bool = False

    CHAT_EXPORT_CONTACTS: bool = True
    CHAT_EXPORT_BOT_CHATS: bool = True
    CHAT_EXPORT_PERSONAL_CHATS: bool = True
    CHAT_EXPORT_PUBLIC_CHANNELS: bool = False
    CHAT_EXPORT_PUBLIC_GROUPS: bool = False
    CHAT_EXPORT_PRIVATE_CHANNELS: bool = True
    CHAT_EXPORT_PRIVATE_GROUPS: bool = True

    JSON_FILE_PAGE_SIZE: Optional[int] = None

    EXPORT_DATE_RANGE: str = "all"
    EXPORT_FROM_DATE: Optional[str] = "2013-08-14"
    EXPORT_TO_DATE: Optional[str] = "2025-06-10"
    MESSAGES_LIMIT: int = 1000

    BASE_DIR: ClassVar[Path] = Path(__file__).resolve().parent.parent

    class Config:
        env_file = ".env"

    @field_validator("CHAT_IDS", mode="before")
    def parse_chat_ids(cls, v):
        import json
        if isinstance(v, str):
            return json.loads(v)
        return v
    
    @field_validator("JSON_FILE_PAGE_SIZE", mode="before")
    def parse_json_page_size(cls, v):
        if isinstance(v, str) and v.strip().lower() in ("", "none", "null"):
            return None
        return int(v)

    @validator("*", pre=True)
    def parse_bool(cls, v):
        if isinstance(v, str):
            if v.lower() in ('true', '1', 't'):
                return True
            elif v.lower() in ('false', '0', 'f'):
                return False
        return v


settings = Settings()