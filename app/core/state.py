from pydantic import BaseModel, Field, validator
from typing import List, Optional, Literal
from app.config import settings

class ExportConfig(BaseModel):
    """Configuration model for Telegram export service.
    This model holds all necessary parameters for exporting data from Telegram chats.
    It includes API credentials, chat IDs, export date range, media types, and chat types.
    The model is initialized with default values from the settings module.
    """
    session_string: str = ""  # Default empty string, can be set later
    api_id: int = settings.API_ID
    api_hash: str = settings.API_HASH

    chat_ids: List[str] = settings.CHAT_IDS or []
    export_date_range: Literal["week", "month", "year", "custom", "limited", "all"] = settings.EXPORT_DATE_RANGE
    from_date: Optional[str] = settings.EXPORT_FROM_DATE
    to_date: Optional[str] = settings.EXPORT_TO_DATE
    messages_limit: int = settings.MESSAGES_LIMIT

    media_export_audios: bool = settings.MEDIA_EXPORT_AUDIOS
    media_export_videos: bool = settings.MEDIA_EXPORT_VIDEOS
    media_export_photos: bool = settings.MEDIA_EXPORT_PHOTOS
    media_export_stickers: bool = settings.MEDIA_EXPORT_STICKERS
    media_export_animations: bool = settings.MEDIA_EXPORT_ANIMATIONS
    media_export_documents: bool = settings.MEDIA_EXPORT_DOCUMENTS
    media_export_voice_messages: bool = settings.MEDIA_EXPORT_VOICE_MESSAGES
    media_export_video_messages: bool = settings.MEDIA_EXPORT_VIDEO_MESSAGES
    media_export_contacts: bool = settings.MEDIA_EXPORT_CONTACTS

    chat_export_contacts: bool = settings.CHAT_EXPORT_CONTACTS
    chat_export_bot_chats: bool = settings.CHAT_EXPORT_BOT_CHATS
    chat_export_personal_chats: bool = settings.CHAT_EXPORT_PERSONAL_CHATS
    chat_export_public_channels: bool = settings.CHAT_EXPORT_PUBLIC_CHANNELS
    chat_export_public_groups: bool = settings.CHAT_EXPORT_PUBLIC_GROUPS
    chat_export_private_channels: bool = settings.CHAT_EXPORT_PRIVATE_CHANNELS
    chat_export_private_groups: bool = settings.CHAT_EXPORT_PRIVATE_GROUPS

    json_file_page_size: Optional[int] = settings.JSON_FILE_PAGE_SIZE

    base_dir: str = settings.BASE_DIR
    session_name: str = "new_session"

    @validator("chat_ids", pre=True)
    def ensure_chat_ids_are_ints(cls, v):
        if isinstance(v, list):
            return [int(i) for i in v if i]
        return []

# CURRENT_CONFIG: Optional[ExportConfig] = None
CURRENT_CONFIG: Optional[ExportConfig] = ExportConfig()