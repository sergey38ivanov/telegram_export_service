import os
import json
import time
from datetime import datetime, timedelta
import uuid
from typing import Union
import shutil
import asyncio
from pathlib import Path
from multiprocessing import Process


from pyrogram import Client, utils
from pyrogram.types import Message
from pyrogram.enums import ChatType, MessageEntityType
from pyrogram.types import User

from app.core.chats import Chat
from app.core.state import CURRENT_CONFIG, ExportConfig
from app.core.utils import sse_log


# API_ID = CURRENT_CONFIG.api_id
# API_HASH = CURRENT_CONFIG.api_hash
# MEDIA_EXPORT = {
#     'audios': CURRENT_CONFIG.media_export_audios,
#     'videos': CURRENT_CONFIG.media_export_videos,
#     'photos': CURRENT_CONFIG.media_export_photos,
#     'stickers': CURRENT_CONFIG.media_export_stickers,
#     'animations': CURRENT_CONFIG.media_export_animations,
#     'documents': CURRENT_CONFIG.media_export_documents,
#     'voice_messages': CURRENT_CONFIG.media_export_voice_messages,
#     'video_messages': CURRENT_CONFIG.media_export_video_messages,
#     'contacts': CURRENT_CONFIG.media_export_contacts
# }
# CHAT_EXPORT = {
#     'contacts': CURRENT_CONFIG.chat_export_contacts,
#     'bot_chats': CURRENT_CONFIG.chat_export_bot_chats,
#     'personal_chats': CURRENT_CONFIG.chat_export_personal_chats,
#     'public_channels': CURRENT_CONFIG.chat_export_public_channels,
#     'public_groups': CURRENT_CONFIG.chat_export_public_groups,
#     'private_channels': CURRENT_CONFIG.chat_export_private_channels,
#     'private_groups': CURRENT_CONFIG.chat_export_private_groups
# }
# CHAT_IDS = CURRENT_CONFIG.chat_ids
# FILE_NOT_FOUND = '(File not included. Change data exporting settings to download.)'
# JSON_FILE_PAGE_SIZE = CURRENT_CONFIG.json_file_page_size
# EXPORT_DATE_RANGE = CURRENT_CONFIG.export_date_range
# EXPORT_FROM_DATE = CURRENT_CONFIG.from_date
# EXPORT_TO_DATE = CURRENT_CONFIG.to_date
# SESSION_STRING = CURRENT_CONFIG.session_string

# now = datetime.now()
# range_type = EXPORT_DATE_RANGE.lower()

# if range_type == "week":
#     from_date = now - timedelta(weeks=1)
#     to_date = now
# elif range_type == "month":
#     from_date = now - timedelta(weeks=4)
#     to_date = now
# elif range_type == "year":
#     from_date = now - timedelta(days=365)
#     to_date = now
# elif range_type == "custom":
#     from_date = datetime.strptime(EXPORT_FROM_DATE, "%Y-%m-%d")
#     to_date = datetime.strptime(EXPORT_TO_DATE, "%Y-%m-%d") if EXPORT_TO_DATE else now
# elif range_type == "limited":
#     LIMIT = 10000
#     from_date = datetime.strptime("2013-08-14", "%Y-%m-%d")  # 2013-08-14
#     to_date = datetime.now()
# else:
#     from_date = datetime.strptime("2013-08-14", "%Y-%m-%d")  # 2013-08-14
#     to_date = datetime.now()

# print(f"Export  range: {range_type}")
# print(f"Export date range: {from_date.strftime('%Y-%m-%d')} to {to_date.strftime('%Y-%m-%d')}")

class Archive:
    def __init__(self, chat_ids: list = [], root_dir: str = ''):
        self.chat_ids = chat_ids
        self.voice_num = 0
        self.photo_num = 0
        self.contact_num = 0
        self.video_message_num = 0
        self.username = ''
        self.messages = []
        self.chat_data = {}
        self.root_dir = root_dir

        self.personal_chat_stats = []  # список словників зі статистикою
        self.chat_type_counters = {
            'personal_chats': 0,
            'private_channels': 0,
            'private_groups': 0,
            'public_channels': 0,
            'public_groups': 0
        }
        self.avatar_path = None
        self.last_activity = None

    def fill_chat_data(self, chat: Chat) -> None:
        self.messages = []
        self.username = chat.username
        match chat.type:
            case ChatType.PRIVATE:
                # TODO: lastname
                self.chat_data['name'] = chat.first_name
                self.chat_data['type'] = 'personal_chat'
                self.chat_data['id'] = chat.id
                self.chat_type_counters['personal_chats'] += 1
            case ChatType.CHANNEL:
                self.chat_data['name'] = chat.title
                self.chat_data['type'] = 'public_channel'
                # when using telegram api ids have -100 prefix
                # https://stackoverflow.com/questions/33858927/how-to-obtain-the-chat-id-of-a-private-telegram-channel
                self.chat_data['id'] = str(chat.id)[4::] if str(chat.id).startswith('-100') else chat.id
                self.chat_type_counters['public_channels'] += 1
            case ChatType.GROUP:
                self.chat_data['name'] = chat.title
                self.chat_data['type'] = 'public_group'
                self.chat_data['id'] = str(chat.id)[4::] if str(chat.id).startswith('-100') else chat.id
                self.chat_type_counters['public_groups'] += 1
            case ChatType.SUPERGROUP:
                self.chat_data['name'] = chat.title
                self.chat_data['type'] = 'public_supergroup'
                self.chat_data['id'] = str(chat.id)[4::] if str(chat.id).startswith('-100') else chat.id
                self.chat_type_counters['public_groups'] += 1
            # TODO: private SUPERGROUP and GROUP
            case _:
                # bot? other chat types
                pass

        # if chat.photo:
        #     chat_export_date = datetime.now().strftime("%Y-%m-%d")
        #     chat_export_dir = f'{self.root_dir}/ChatExport_{chat.id}_{self.username}_{chat_export_date}'
        #     avatar_path = f"{chat_export_dir}/avatar.jpg"
        #     self.avatar_path = avatar_path

        #     try:
        #         # avatar_full_path = os.path.join(self.root_dir, self.chat_data['name'], 'avatar.jpg')
        #         avatar_full_path = os.path.join(chat_export_dir, 'avatar.jpg')

        #         asyncio.create_task(client_app.download_media(chat.photo.small_file_id, file_name=avatar_full_path))
        #     except:
        #         self.avatar_path = None
        


    async def process_message(self, chat, message, msg_info: dict) -> None:
        # TODO: move msg_info filling to other function
        msg_info['id'] = message.id
        msg_info['type'] = 'message'
        msg_info['date'] = message.date.strftime('%Y-%m-%dT%H:%M:%S')
        msg_info['date_unixtime'] = convert_to_unixtime(message.date)
        self.last_activity = message.date.strftime('%Y-%m-%dT%H:%M:%S')
        # set chat name
        # this part is so shitty fix THIS
        if chat.type == ChatType.PRIVATE:
            full_name = ''
            if message.from_user.first_name is not None:
                full_name += message.from_user.first_name
            if message.from_user.last_name is not None:
                full_name += f' {message.from_user.last_name}'
            msg_info['from'] = full_name
            msg_info['from_id'] = f'user{message.from_user.id}'
        else:
            msg_info['from'] = chat.title
            # TODO: is this correct for groups?
            if chat.type == ChatType.CHANNEL:
                if str(message.sender_chat.id).startswith('-100'):
                    msg_info['from_id'] = f'channel{str(message.sender_chat.id)[4::]}'
                else:
                    msg_info['from_id'] = f'channel{str(message.sender_chat.id)}'
            else:
                pass
                # TODO: use from user...

        if message.reply_to_message_id is not None:
            msg_info['reply_to_message_id'] = message.reply_to_message_id

        if message.forward_from_chat is not None:
            msg_info['forwarded_from'] = message.forward_from_chat.title
        elif message.forward_from is not None:
            msg_info['forwarded_from'] = message.forward_from.first_name

        # TODO: type service. actor...

        if message.sticker is not None:
            # if MEDIA_EXPORT['stickers'] is True:
            if CURRENT_CONFIG.media_export_stickers is True:    
                names = get_sticker_name(
                    message,
                    self.username,
                    chat.id,
                    self.root_dir
                )
                await get_sticker_data(message, msg_info, names)
            else:
                msg_info['file'] = FILE_NOT_FOUND
                msg_info['thumbnail'] = FILE_NOT_FOUND
                msg_info['media_type'] = 'sticker'
                msg_info['sticker_emoji'] = message.sticker.emoji
                msg_info['width'] = message.sticker.width
                msg_info['height'] = message.sticker.height
        elif message.animation is not None:
            # if MEDIA_EXPORT['animations'] is True:
            if CURRENT_CONFIG.media_export_animations is True:
                names = get_animation_name(message, self.username, chat.id, self.root_dir)
                await get_animation_data(
                    message,
                    msg_info,
                    names
                )
            else:
                msg_info['file'] = FILE_NOT_FOUND
                msg_info['thumbnail'] = FILE_NOT_FOUND
                msg_info['media_type'] = 'animation'
                msg_info['mime_type'] = message.animation.mime_type
                msg_info['width'] = message.animation.width
        elif message.photo is not None:
            # if MEDIA_EXPORT['photos'] is True:
            print("PHOTO")
            if CURRENT_CONFIG.media_export_photos is True:
                print("PHOTO TRUE")
                self.photo_num += 1
                names = get_photo_name(
                    message,
                    self.username,
                    chat.id,
                    self.root_dir,
                    self.photo_num
                )
                await get_photo_data(
                    message,
                    msg_info,
                    names
                )
            else:
                msg_info['photo'] = FILE_NOT_FOUND
                msg_info['width'] = message.photo.width
                msg_info['height'] = message.photo.height
        elif message.video is not None:
            # if MEDIA_EXPORT['videos'] is True:
            if CURRENT_CONFIG.media_export_videos is True:
                names = get_video_name(message, self.username, chat.id, self.root_dir)
                await get_video_data(message, msg_info, names)
            else:
                msg_info['file'] = FILE_NOT_FOUND
                msg_info['thumbnail'] = FILE_NOT_FOUND
                msg_info['media_type'] = 'video_file'
                msg_info['mime_type'] = message.video.mime_type
                msg_info['duration_seconds'] = message.video.duration
                msg_info['width'] = message.video.width
        elif message.video_note is not None:
            # if MEDIA_EXPORT['video_messages'] is True:
            if CURRENT_CONFIG.media_export_video_messages is True:
                self.video_message_num += 1
                names = get_video_note_name(
                    message,
                    self.username,
                    chat.id,
                    self.root_dir,
                    self.video_message_num
                )
                await get_video_note_data(
                    message,
                    msg_info,
                    names
                )
            else:
                msg_info['file'] = FILE_NOT_FOUND
                msg_info['thumbnail'] = FILE_NOT_FOUND
                msg_info['media_type'] = 'video_message'
                msg_info['mime_type'] = message.video_note.mime_type
                msg_info['duration_seconds'] = message.video_note.duration
        elif message.audio is not None:
            # if MEDIA_EXPORT['audios'] is True:
            if CURRENT_CONFIG.media_export_audios is True:
                names = get_audio_name(message, self.username, chat.id, self.root_dir)
                await get_audio_data(message, msg_info, names)
            else:
                msg_info['file'] = FILE_NOT_FOUND
                msg_info['thumbnail'] = FILE_NOT_FOUND
                msg_info['media_type'] = 'audio_file'
                msg_info['performer'] = message.audio.performer
                msg_info['title'] = message.audio.title
                msg_info['mime_type'] = message.audio.mime_type
        elif message.voice is not None:
            # if MEDIA_EXPORT['voice_messages'] is True:
            if CURRENT_CONFIG.media_export_voice_messages is True:
                self.voice_num += 1
                names = get_voice_name(
                    message,
                    self.username,
                    chat.id,
                    self.root_dir,
                    self.voice_num
                )
                await get_voice_data(
                    message,
                    msg_info,
                    names
                )
            else:
                msg_info['file'] = FILE_NOT_FOUND
        elif message.document is not None:
            # if MEDIA_EXPORT['documents'] is True:
            if CURRENT_CONFIG.media_export_documents is True:
                names = get_document_name(message, self.username, chat.id, self.root_dir)
                await get_document_data(
                    message,
                    msg_info,
                    names
                )
            else:
                msg_info['file'] = FILE_NOT_FOUND
                msg_info['thumbnail'] = FILE_NOT_FOUND
        elif message.contact is not None:
            self.contact_num += 1
            names = get_contact_name(
                self.username,
                chat.id,
                self.root_dir,
                self.contact_num
            )
            get_contact_data(
                message,
                msg_info,
                names
            )
        elif message.location is not None:
            msg_info['location_information'] = {
                'latitude': message.location.latitude,
                'longitude': message.location.longitude
            }

        if message.text is not None:
            text = get_text_data(message, 'text')
            if text:
                text.append(message.text)
                msg_info['text'] = text
            else:
                msg_info['text'] = message.text
        elif message.caption is not None:
            caption = get_text_data(message, 'caption')
            if caption:
                caption.append(message.caption)
                msg_info['caption'] = caption
            else:
                msg_info['caption'] = message.caption
        else:
            msg_info['text'] = ''
        self.messages.append(msg_info)
        self.chat_data['messages'] = self.messages

        # оновити лічильники для персональних чатів
        # if self.chat_data['type'] == 'personal_chat':
        if True:
            stat = next((item for item in self.personal_chat_stats if item['user_id'] == chat.id), None)
            if stat is None:
                stat = {
                    "chat_name": chat.first_name or '',
                    "user_id": chat.id,
                    "avatar": self.avatar_path,
                    "last_activity": self.last_activity,
                    "message_count": 0,
                    "photos": 0,
                    "videos": 0,
                    "audios": 0,
                    "documents": 0,
                    "voice_messages": 0,
                    "video_messages": 0
                }
                self.personal_chat_stats.append(stat)
            stat['message_count'] += 1
            if message.photo: stat['photos'] += 1
            if message.video: stat['videos'] += 1
            if message.audio: stat['audios'] += 1
            if message.document: stat['documents'] += 1
            if message.voice: stat['voice_messages'] += 1
            if message.video_note: stat['video_messages'] += 1

def generate_json_name(username: str, user_id: str, path: str = '', page_idx: int = 1) -> str:
    # TODO: add path when user want other path
    chat_export_date = datetime.now().strftime("%Y-%m-%d")
    chat_export_name = f'{path}/ChatExport_{user_id}_{username}_{chat_export_date}'
    json_name = f'{chat_export_name}/result_{page_idx}.json'
    os.makedirs(chat_export_name, exist_ok=True)
    return json_name


async def get_sticker_data(
    message: Message,
    msg_info: dict,
    names: tuple
) -> None:
    sticker_path, thumb_path, sticker_relative_path, thumb_relative_path = names
    try:
        await client_app.download_media(
            message.sticker.file_id,
            sticker_path
        )
        msg_info['file'] = sticker_relative_path
    except ValueError:
        print("Oops can't download media!")
        msg_info['file'] = FILE_NOT_FOUND

    if message.sticker.thumbs is not None:
        try:
            await client_app.download_media(
                message.sticker.thumbs[0].file_id,
                thumb_path
            )
            msg_info['thumbnail'] = thumb_relative_path
        except ValueError:
            print("Oops can't download media!")
            msg_info['thumbnail'] = FILE_NOT_FOUND
    else:
        msg_info['thumbnail'] = FILE_NOT_FOUND

    msg_info['media_type'] = 'sticker'
    msg_info['sticker_emoji'] = message.sticker.emoji
    msg_info['width'] = message.sticker.width
    msg_info['height'] = message.sticker.height


async def get_animation_data(
    message: Message,
    msg_info: dict,
    names: tuple
) -> None:
    animation_path, thumb_path, animation_relative_path, thumb_relative_path = names
    try:
        await client_app.download_media(
            message.animation.file_id,
            animation_path
        )
        msg_info['file'] = animation_relative_path
    except ValueError:
        print("Oops can't download media!")
        msg_info['file'] = FILE_NOT_FOUND

    if message.animation.thumbs is not None:
        try:
            await client_app.download_media(
                message.animation.thumbs[0].file_id,
                thumb_path
            )
        except ValueError:
            print("Oops can't download media!")
            msg_info['thumbnail'] = FILE_NOT_FOUND
    else:
        msg_info['thumbnail'] = FILE_NOT_FOUND

    msg_info['media_type'] = 'animation'
    msg_info['mime_type'] = message.animation.mime_type
    msg_info['width'] = message.animation.width
    msg_info['height'] = message.animation.height


async def get_photo_data(
    message: Message,
    msg_info: dict,
    names: tuple
):
    print("GET PHOTO DATA")
    
    photo_path, photo_relative_path = names
    print(photo_path)
    print(photo_relative_path)
    # try:
    if True:
        result_path = await client_app.download_media(
            message.photo.file_id,
            photo_path
        )
        msg_info['photo'] = photo_relative_path

        print(result_path)
    # except ValueError:
    #     print("Oops can't download media!")
    #     msg_info['photo'] = FILE_NOT_FOUND

    msg_info['width'] = message.photo.width
    msg_info['height'] = message.photo.height


async def get_video_data(
    message: Message,
    msg_info: dict,
    names: tuple
) -> None:
    video_path, thumb_path, video_relative_path, thumb_relative_path = names
    try:
        await client_app.download_media(
            message.video.file_id,
            video_path
        )
        msg_info['file'] = video_relative_path
    except ValueError:
        print("Oops can't download media!")
        msg_info['file'] = FILE_NOT_FOUND

    if message.video.thumbs is not None:
        try:
            await client_app.download_media(
                message.video.thumbs[0].file_id,
                thumb_path
            )
            msg_info['thumbnail'] = thumb_relative_path
        except ValueError:
            print("Oops can't download media!")
            msg_info['thumbnail'] = FILE_NOT_FOUND
    else:
        msg_info['thumbnail'] = FILE_NOT_FOUND

    msg_info['media_type'] = 'video_file'
    msg_info['mime_type'] = message.video.mime_type
    msg_info['duration_seconds'] = message.video.duration
    msg_info['width'] = message.video.width
    msg_info['height'] = message.video.height


async def get_video_note_data(
    message: Message,
    msg_info: dict,
    names: tuple
):
    vnote_path, thumb_path, vnote_relative_path, thumb_relative_path = names
    try:
        await client_app.download_media(
            message.video_note.file_id,
            vnote_path
        )
        msg_info['file'] = vnote_relative_path
    except ValueError:
        print("Oops can't download media!")
        msg_info['file'] = FILE_NOT_FOUND

    if message.video_note.thumbs is not None:
        try:
            await client_app.download_media(
                message.video_note.thumbs[0].file_id,
                thumb_path
            )
            msg_info['thumbnail'] = thumb_relative_path
        except ValueError:
            print("Oops can't download media!")
            msg_info['thumbnail'] = FILE_NOT_FOUND
    else:
        msg_info['thumbnail'] = FILE_NOT_FOUND

    msg_info['media_type'] = 'video_message'
    msg_info['mime_type'] = message.video_note.mime_type
    msg_info['duration_seconds'] = message.video_note.duration


async def get_audio_data(
    message: Message,
    msg_info: dict,
    names: tuple
) -> None:
    audio_path, thumb_path, audio_relative_path, thumb_relative_path = names
    try:
        await client_app.download_media(
            message.audio.file_id,
            audio_path
        )
        msg_info['file'] = audio_relative_path
    except ValueError:
        print("Oops can't download media!")
        msg_info['file'] = FILE_NOT_FOUND

    if message.audio.thumbs is not None:
        try:
            await client_app.download_media(
                message.audio.thumbs[0].file_id,
                thumb_path
            )
            msg_info['thumbnail'] = thumb_relative_path
        except ValueError:
            print("Oops can't download media!")
            msg_info['thumbnail'] = FILE_NOT_FOUND
    else:
        msg_info['thumbnail'] = FILE_NOT_FOUND

    msg_info['media_type'] = 'audio_file'
    msg_info['performer'] = message.audio.performer
    msg_info['title'] = message.audio.title
    msg_info['mime_type'] = message.audio.mime_type
    msg_info['duration_seconds'] = message.audio.duration


async def get_voice_data(
    message: Message,
    msg_info: dict,
    names: tuple
) -> None:
    voice_path, voice_relative_path = names
    try:
        await client_app.download_media(
            message.voice.file_id,
            voice_path
        )
        msg_info['file'] = voice_relative_path
    except ValueError:
        print("Oops can't download media!")
        msg_info['file'] = FILE_NOT_FOUND

    msg_info['media_type'] = 'voice_message'
    msg_info['mime_type'] = message.voice.mime_type
    msg_info['duration_seconds'] = message.voice.duration


async def get_document_data(
    message: Message,
    msg_info: dict,
    names: tuple
) -> None:
    doc_path, thumb_path, doc_relative_path, thumb_relative_path = names
    try:
        await client_app.download_media(
            message.document.file_id,
            doc_path
        )
        msg_info['file'] = doc_relative_path
    except ValueError:
        print("Oops can't download media!")
        msg_info['file'] = FILE_NOT_FOUND

    if message.document.thumbs is not None:
        try:
            await client_app.download_media(
                message.document.thumbs[0].file_id,
                thumb_path
            )
            msg_info['thumbnail'] = thumb_relative_path
        except ValueError:
            print("Oops can't download media!")
            msg_info['thumbnail'] = FILE_NOT_FOUND
    else:
        msg_info['thumbnail'] = FILE_NOT_FOUND

    msg_info['mime_type'] = message.document.mime_type


def get_text_data(message: Message, text_mode: str) -> list:
    text = []
    if text_mode == 'caption':
        if message.caption_entities is not None:
            entities = message.caption_entities
        else:
            return text
    elif text_mode == 'text':
        if message.text.entities is not None:
            entities = message.text.entities
        else:
            return text

    for e in entities:
        txt = {}
        match e.type:
            case MessageEntityType.URL:
                txt['type'] = 'link'
            case MessageEntityType.HASHTAG:
                txt['type'] = 'hashtag'
            case MessageEntityType.CASHTAG:
                txt['type'] = 'cashtag'
            case MessageEntityType.BOT_COMMAND:
                txt['type'] = 'bot_command'
            case MessageEntityType.MENTION:
                txt['type'] = 'mention'
            case MessageEntityType.EMAIL:
                txt['type'] = 'email'
            case MessageEntityType.PHONE_NUMBER:
                txt['type'] = 'phone_number'
            case MessageEntityType.BOLD:
                txt['type'] = 'bold'
            case MessageEntityType.ITALIC:
                txt['type'] = 'italic'
            case MessageEntityType.UNDERLINE:
                txt['type'] = 'underline'
            case MessageEntityType.STRIKETHROUGH:
                txt['type'] = 'strikethrough'
            case MessageEntityType.SPOILER:
                txt['type'] = 'spoiler'
            case MessageEntityType.CODE:
                txt['type'] = 'code'
            case MessageEntityType.PRE:
                txt['type'] = 'pre'
                txt['language'] = ''
            case MessageEntityType.BLOCKQUOTE:
                txt['type'] = 'blockquote'
            case MessageEntityType.TEXT_LINK:
                txt['type'] = 'text_link'
                txt['href'] = e.url
            case MessageEntityType.TEXT_MENTION:
                txt['type'] = 'text_mention'
            case MessageEntityType.BANK_CARD:
                txt['type'] = 'bank_card'
            case MessageEntityType.CUSTOM_EMOJI:
                txt['type'] = 'custom_emoji'
            case _:
                txt['type'] = 'unknown'

        if text_mode == 'text':
            txt['text'] = message.text[e.offset:e.offset + e.length]
        else:
            txt['text'] = message.caption[e.offset:e.offset + e.length]
        text.append(txt)
    return text

    
# TODO: fix better typing
def get_contact_data(
    message: Message,
    msg_info: dict,
    names: tuple
) -> list:
    contact_data = {'phone_number': message.contact.phone_number}
    contact_data['fist_name'] =  message.contact.first_name if message.contact.first_name is not None else ''
    contact_data['last_name'] =  message.contact.last_name if message.contact.last_name is not None else ''
    msg_info['contact_information'] = contact_data

    # if MEDIA_EXPORT['contacts'] is True:
    if CURRENT_CONFIG.chat_export_contacts is True:
        vcard_path, vcard_relative_path = names
        msg_info['contact_vcard'] = vcard_relative_path

        # convert to vcard
        vcard = (
            'BEGIN:VCARD\n'
            'VERSION:3.0\n'
            f'FN;CHARSET=UTF-8:{message.contact.first_name} {message.contact.last_name}\n'
            f'N;CHARSET=UTF-8:{message.contact.last_name};{message.contact.first_name};;;\n'
            f'TEL;TYPE=CELL:{message.contact.phone_number}\n'
            'END:VCARD\n'
        ) 
        with open(vcard_path, 'w', encoding="utf-8") as f:
            f.write(vcard)
    else:
        msg_info['contact_vcard'] = FILE_NOT_FOUND


def get_photo_name(
    message: Message,
    username: str,
    user_id: str,
    path: str = '',
    media_num: int = None
) -> tuple:
    print("GET PHOTO")
    chat_export_date = datetime.now().strftime("%Y-%m-%d")
    chat_export_name = f'ChatExport_{user_id}_{username}_{chat_export_date}'
    # # TODO: when user want other path
    # path = ''
    media_dir = f'{path}/{chat_export_name}/photos'
    os.makedirs(media_dir, exist_ok=True)

    date = message.date.strftime('%d-%m-%Y_%H-%M-%S')
    # TODO: what format for png??
    photo_name = f'file_{media_num}@{date}.jpg'
    photo_path = f'{path}/{chat_export_name}/photos/{photo_name}'
    photo_relative_path = f'photos/{photo_name}'

    result = photo_path, photo_relative_path
    return result


def get_video_name(
    message: Message,
    username: str,
    chat_id,
    path: str = '',
    media_num: int = None
) -> tuple:
    chat_export_date = datetime.now().strftime("%Y-%m-%d")
    chat_export_name = f'ChatExport_{chat_id}_{username}_{chat_export_date}'
    # # TODO: when user want other path
    # path = ''
    media_dir = f'{path}/{chat_export_name}/video_files'
    os.makedirs(media_dir, exist_ok=True)

    # TODO: gen better way random str
    video_name = str(uuid.uuid4()) if message.video.file_name is None else message.video.file_name
    video_path = f'{media_dir}/{video_name}'

    if message.video.thumbs is not None:
        thumb_name = f'{video_name}_thumb.jpg'
        thumb_path = f'{media_dir}/{thumb_name}'
    else:
        thumb_name = None
        thumb_path = None

    video_relative_path = f'video_files/{video_name}'
    thumb_relative_path = None if thumb_name is None else f'video_files/{thumb_name}'

    result = (
        video_path,
        thumb_path,
        video_relative_path,
        thumb_relative_path
    )
    return result


def get_voice_name(
    message: Message,
    username: str,
    chat_id,
    path: str = '',
    media_num: int = None
) -> tuple:
    chat_export_date = datetime.now().strftime("%Y-%m-%d")
    chat_export_name = f'ChatExport_{chat_id}_{username}_{chat_export_date}'

    media_dir = f'{path}/{chat_export_name}/voice_messages'
    os.makedirs(media_dir, exist_ok=True)

    date = message.date.strftime('%d-%m-%Y_%H-%M-%S')
    voice_name = f'audio_{media_num}@{date}.ogg'
    voice_path = f'{media_dir}/{voice_name}'
    voice_relative_path = f'voice_messages/{voice_name}'

    result = voice_path, voice_relative_path
    return result


def get_video_note_name(
    message: Message,
    username: str,
    chat_id,
    path: str = '',
    media_num: int = None
) -> tuple:
    chat_export_date = datetime.now().strftime("%Y-%m-%d")
    chat_export_name = f'ChatExport_{chat_id}_{username}_{chat_export_date}'

    media_dir = f'{path}/{chat_export_name}/round_video_messages'
    os.makedirs(media_dir, exist_ok=True)

    # TODO: by default don't have name
    date = message.date.strftime('%d-%m-%Y_%H-%M-%S')
    vnote_name = f'file_{media_num}@{date}.mp4'
    vnote_path = f'{media_dir}/{vnote_name}'

    if message.video_note.thumbs is not None:
        thumb_name = f'{vnote_name}_thumb.jpg'
        thumb_path = f'{media_dir}/{thumb_name}'
    else:
        thumb_name = None
        thumb_path = None

    vnote_relative_path = f'round_video_messages/{vnote_name}'
    thumb_relative_path = None if thumb_name is None else f'round_video_messages/{thumb_name}'

    result = (
        vnote_path,
        thumb_path,
        vnote_relative_path,
        thumb_relative_path
    )
    return result


def get_sticker_name(
    message: Message,
    username: str,
    chat_id,
    path: str = '',
    media_num: int = None
) -> tuple:
    chat_export_date = datetime.now().strftime("%Y-%m-%d")
    chat_export_name = f'ChatExport_{chat_id}_{username}_{chat_export_date}'

    media_dir = f'{path}/{chat_export_name}/stickers'
    os.makedirs(media_dir, exist_ok=True)
    # TODO: gen better way random str
    sticker_name = str(uuid.uuid4()) if message.sticker.file_name is None else message.sticker.file_name
    sticker_path = f'{media_dir}/{sticker_name}'

    if message.sticker.thumbs is not None:
        thumb_name = f'{sticker_name}_thumb.jpg'
        thumb_path = f'{media_dir}/{thumb_name}'
    else:
        thumb_name = None
        thumb_path = None

    sticker_relative_path = f'stickers/{sticker_name}'
    thumb_relative_path = None if thumb_name is None else f'stickers/{thumb_name}'

    result = (
        sticker_path,
        thumb_path,
        sticker_relative_path,
        thumb_relative_path
    )
    return result


def get_animation_name(
    message: Message,
    username: str,
    chat_id,
    path: str = '',
    media_num: int = None
) -> tuple:
    chat_export_date = datetime.now().strftime("%Y-%m-%d")
    chat_export_name = f'ChatExport_{chat_id}_{username}_{chat_export_date}'

    media_dir = f'{path}/{chat_export_name}/video_files'
    os.makedirs(media_dir, exist_ok=True)

    # TODO: gen better way random str
    animation_name = str(uuid.uuid4()) if message.animation.file_name is None else message.animation.file_name
    animation_path = f'{media_dir}/{animation_name}'

    if message.animation.thumbs is not None:
        thumb_name = f'{animation_name}_thumb.jpg'
        thumb_path = f'{media_dir}/{thumb_name}'
    else:
        thumb_name = None
        thumb_path = None

    animation_relative_path = f'video_files/{animation_name}'
    thumb_relative_path = None if thumb_name is None else f'video_files/{thumb_name}'
    result = (
        animation_path,
        thumb_path,
        animation_relative_path,
        thumb_relative_path
    )
    return result


def get_audio_name(
    message: Message,
    username: str,
    chat_id,
    path: str = '',
    media_num: int = None
) -> tuple:
    chat_export_date = datetime.now().strftime("%Y-%m-%d")
    chat_export_name = f'ChatExport_{chat_id}_{username}_{chat_export_date}'

    media_dir = f'{path}/{chat_export_name}/files'
    os.makedirs(media_dir, exist_ok=True)

    # TODO: gen better way random str
    audio_name = str(uuid.uuid4()) if message.audio.file_name is None else message.audio.file_name
    audio_path = f'{media_dir}/{audio_name}'

    if message.audio.thumbs is not None:
        thumb_name = f'{audio_name}_thumb.jpg'
        thumb_path = f'{media_dir}/{thumb_name}'
    else:
        thumb_name = None
        thumb_path = None

    audio_relative_path = f'files/{audio_name}'
    thumb_relative_path = None if thumb_name is None else f'files/{thumb_name}'

    result = audio_path, thumb_path, audio_relative_path, thumb_relative_path
    return result


def get_document_name(
    message: Message,
    username: str,
    chat_id,
    path: str = '',
    media_num: int = None
) -> tuple:
    chat_export_date = datetime.now().strftime("%Y-%m-%d")
    chat_export_name = f'ChatExport_{chat_id}_{username}_{chat_export_date}'

    media_dir = f'{path}/{chat_export_name}/files'
    os.makedirs(media_dir, exist_ok=True)

    # TODO: gen better way random str
    doc_name = str(uuid.uuid4()) if message.document.file_name is None else message.document.file_name
    doc_path = f'{media_dir}/{doc_name}'

    if message.document.thumbs is not None:
        thumb_name = f'{doc_name}_thumb.jpg'
        thumb_path = f'{media_dir}/{thumb_name}'
    else:
        thumb_name = None
        thumb_path = None

    doc_relative_path = f'files/{doc_name}'
    thumb_relative_path = None if thumb_name is None else f'files/{thumb_name}'

    result = doc_path, thumb_path, doc_relative_path, thumb_relative_path
    return result


def get_contact_name(
    username: str,
    chat_id,
    path: str = '',
    media_num: int = 0,
) -> tuple:
    chat_export_date = datetime.now().strftime("%Y-%m-%d")
    chat_export_name = f'ChatExport_{chat_id}_{username}_{chat_export_date}'

    media_dir = f'{path}/{chat_export_name}/contacts'
    os.makedirs(media_dir, exist_ok=True)
    contact_name = f'contact_{media_num}.vcf'
    contact_path = f'{media_dir}/{contact_name}'
    contact_relative_path = f'contacts/{contact_name}'
    return contact_path, contact_relative_path


def convert_to_unixtime(date: datetime):
    # telegram date format: "2022-07-10 08:49:23"
    unix_time = int(time.mktime(date.timetuple()))
    return unix_time


def to_html():
    pass


# def split_json_file(data: dict, output_path: str, page_size: int = JSON_FILE_PAGE_SIZE):
def split_json_file(data: dict, output_path: str, page_size: int = CURRENT_CONFIG.json_file_page_size):
    messages = data["messages"]
    page = 1
    current_data = {"messages": []}

    for msg in messages:
        current_data["messages"].append(msg)
        serialized_data = json.dumps(current_data, default=str, ensure_ascii=False)
        if len(serialized_data.encode('utf-8')) > page_size:
            # Remove the last message that made it too big
            current_data["messages"].pop()
            # Save current part
            with open(output_path.replace("result.json", f"result_part{page}.json"), "w", encoding="utf-8") as outf:
                json.dump(current_data, outf, indent=4, default=str, ensure_ascii=False)
            # Start new part with the removed message
            page += 1
            current_data = {"messages": [msg]}

    # Save last part
    with open(output_path.replace("result.json", f"result_part{page}.json"), "w", encoding="utf-8") as outf:
        json.dump(current_data, outf, indent=4, default=str, ensure_ascii=False)


async def export_contacts(client_app: Client, ROOT_DIR: str, photo: bool = True):
    contacts_dir = os.path.join(ROOT_DIR, 'contacts')
    os.makedirs(contacts_dir, exist_ok=True)
    photos_dir = os.path.join(contacts_dir, 'photos')
    os.makedirs(photos_dir, exist_ok=True)

    result = []
    download_tasks = []
    sem = asyncio.Semaphore(10)

    contacts = await client_app.get_contacts()
    for idx, user in enumerate(contacts, start=1):
        contact_data = {
            "user_id": user.id,
            "username": user.username or None,
            "first_name": user.first_name or "",
            "last_name": user.last_name or "",
            "phone_number": user.phone_number or None,
            "avatar": None
        }

        if photo:
        # Плануємо завантаження аватара
            if user.photo:
                photo_path = os.path.join(photos_dir, f"photo_{idx}.jpg")
                rel_photo_path = f"contacts/photos/photo_{idx}.jpg"

                async def download(photo_file_id=user.photo.small_file_id, path=photo_path, rel_path=rel_photo_path, contact=contact_data):
                    async with sem:
                        try:
                            await client_app.download_media(photo_file_id, file_name=path)
                            contact["avatar"] = rel_path
                        except Exception:
                            contact["avatar"] = None

                download_tasks.append(download())

        result.append(contact_data)

    # Завантажуємо всі аватарки одночасно
    await asyncio.gather(*download_tasks)

    # Зберігаємо JSON
    json_path = os.path.join(contacts_dir, "contacts.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=4, ensure_ascii=False)

    print(f"[✓] Exported {len(result)} contacts to {json_path}")
    sse_log(f"☎️ Exported {len(result)} contacts")


def safe_rmtree(path, max_retries=5, delay=1):
    for i in range(max_retries):
        try:
            shutil.rmtree(path)
            return True
        except PermissionError as e:
            print(f"[!] Rmtree failed (attempt {i+1}/{max_retries}): {e}")
            time.sleep(delay)
    print(f"[X] Failed to remove {path} after {max_retries} retries.")
    return False

import time

async def main(config: ExportConfig):

    start_time = time.perf_counter()
    async with client_app:
        sse_log("🟢 Експорт розпочато")
        me = await client_app.get_me()
        phone = me.phone_number
        name = me.first_name if me.first_name else ' ' + (me.last_name if me.last_name else '')
        sse_log(f"📱 +{phone} 🚪 {name}")
        ROOT_DIR = str(CURRENT_CONFIG.base_dir / "data" / (phone + name))

        contacts = await export_contacts(client_app, ROOT_DIR, photo = False)

        # if not CHAT_IDS:
        if not CURRENT_CONFIG.chat_ids:
            all_dialogs_id = await Chat(client_app).get_ids(last_message_date=from_date)
            print(all_dialogs_id)
            # CHAT_IDS.extend(all_dialogs_id)
            CURRENT_CONFIG.chat_ids.extend(all_dialogs_id)

        # archive = Archive(CHAT_IDS, ROOT_DIR)
        archive = Archive(CURRENT_CONFIG.chat_ids, ROOT_DIR)
        sse_log(f"💬 Found {len(CURRENT_CONFIG.chat_ids)} chat(s) per last {config.export_date_range}")
        LIMIT = 1000
        # CURRENT_CONFIG.messages_limit = 1000
        # for cid in CHAT_IDS:
        for cid in CURRENT_CONFIG.chat_ids:
            end_date = to_date
            print(f'Processing chat: {cid} \t\t', end='')
            sse_log(f"💬 Processing chat: {cid}")

            
            # when use telegram api, channels id have -100 prefix
            if type(cid) == int and not str(cid).startswith('-100'):
                new_id = int(f'{cid}')
                # CHAT_IDS[CHAT_IDS.index(cid)] = new_id
                CURRENT_CONFIG.chat_ids[CURRENT_CONFIG.chat_ids.index(cid)] = new_id

            chat = await client_app.get_chat(cid)
            archive.fill_chat_data(chat)
            print(chat.first_name, chat.last_name)
            sse_log(f"💬 {chat.first_name} {chat.last_name if chat.last_name else ''}")

            # TODO: add exception for private channels
            # read messages from first to last
            END_INNER_LOOP = False
            while_idx = 1
            while True:
                if END_INNER_LOOP:
                    break
                print(f'\t Processing page {while_idx} \t\t', end='')
                offset_date = end_date if range_type != 'all' else utils.zero_datetime()
                print(offset_date)
                all_messages = [m async for m in client_app.get_chat_history(cid, limit=LIMIT, offset_date=offset_date)]
                # all_messages.reverse()
                print(f'\t {len(all_messages)} messages')
                sse_log(f"📧 {len(all_messages)} messages")

                indx = 0
                m_date = None
                for idx, message in enumerate(all_messages, start=1):
                    indx = idx
                    m_date = message.date
                    # TODO: add initial message of channel
                    msg_info = {}

                    if message.date < from_date:
                        END_INNER_LOOP = True
                        print(f"BREAK: \t {idx} {message.date}")
                        break
                    if message.date > to_date:
                        print(f"CONTINUE: \t {idx}")
                        continue

                    await archive.process_message(chat, message, msg_info)
                if indx < LIMIT and not END_INNER_LOOP:
                    END_INNER_LOOP = True
                    print(f'\t End of chat history reached at message {indx} with date {m_date}')
                end_date = m_date
                while_idx += 1
                print(f'\t Last message date: {end_date}')

                if indx == 1000:
                    json_name = generate_json_name(username=archive.username, user_id=str(cid), path=ROOT_DIR, page_idx=while_idx-1)
                    # if not JSON_FILE_PAGE_SIZE:
                    if not CURRENT_CONFIG.json_file_page_size:
                        with open(json_name, mode='w', encoding="utf-8") as f:
                            json.dump(archive.chat_data, f, indent=4, default=str, ensure_ascii=False)
                    else:
                        # split_json_file(archive.chat_data, json_name, JSON_FILE_PAGE_SIZE)
                        split_json_file(archive.chat_data, json_name, CURRENT_CONFIG.json_file_page_size)
                    archive.messages = []
                    print(f'\t Saved {idx} messages to {json_name}')
                    sse_log(f"\t Saved {idx} messages to {json_name}")

            json_name = generate_json_name(username=archive.username, user_id=str(cid), path=ROOT_DIR, page_idx=while_idx-1)
            if "messages" not in archive.chat_data:
                dir_name = os.path.dirname(json_name)
                safe_rmtree(dir_name)
                continue
            if archive.chat_data['messages'] == []:
                dir_name = os.path.dirname(json_name)
                safe_rmtree(dir_name)
                continue


            # if not JSON_FILE_PAGE_SIZE:
            if not CURRENT_CONFIG.json_file_page_size:
                with open(json_name, mode='w', encoding="utf-8") as f:
                    json.dump(archive.chat_data, f, indent=4, default=str, ensure_ascii=False)
            else:
                # split_json_file(archive.chat_data, json_name, JSON_FILE_PAGE_SIZE)
                split_json_file(archive.chat_data, json_name, CURRENT_CONFIG.json_file_page_size)
            if "messages" in archive.chat_data:
                archive.chat_data['messages'] = []

        summary = {
            "total_contacts": len(await client_app.get_contacts()),
            "total_personal_chats": archive.chat_type_counters['personal_chats'],
            "total_private_channels": archive.chat_type_counters['private_channels'],
            "total_private_groups": archive.chat_type_counters['private_groups'],
            "total_public_channels": archive.chat_type_counters['public_channels'],
            "total_public_groups": archive.chat_type_counters['public_groups'],
            "personal_chats": archive.personal_chat_stats
        }

        summary_path = os.path.join(ROOT_DIR, 'chat_summary.json')
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=4, ensure_ascii=False)
        print(f"[✓] Saved chat summary to {summary_path}")
        sse_log(f"✅ Saved export summary")
        # sse_log(json.dumps(summary, ensure_ascii=False))

     # ⏱ Кінець вимірювання
    end_time = time.perf_counter()
    total_seconds = end_time - start_time
    print(f"[⏱] Total time: {total_seconds:.2f} seconds")
    sse_log(f"⏱️ Total time: {total_seconds:.2f} seconds")
    
    session_path = Path(client_app.name + ".session")
    new_session_path = session_path.with_name(f"{phone}.session")
    
    try:
        session_path.rename(new_session_path)
        print(f"[✓] Session file renamed to {new_session_path.name}")
    except Exception as e:
        print(f"[!] Failed to rename session file: {e}")

    # --- перейменування .session-journal ---
    journal_path = session_path.with_suffix(".session-journal")
    new_journal_path = new_session_path.with_suffix(".session-journal")

    if journal_path.exists():
        try:
            journal_path.rename(new_journal_path)
            print(f"[✓] Journal file renamed to {new_journal_path.name}")
        except Exception as e:
            print(f"[!] Failed to rename journal file: {e}")

    # --- збереження session_string ---
    try:
        session_string_path = new_session_path.with_name(f"{phone}_session_string.txt")
        with open(session_string_path, "w", encoding="utf-8") as f:
            f.write(config.session_string)
        print(f"[✓] Session string saved to {session_string_path.name}")
    except Exception as e:
        print(f"[!] Failed to save session string: {e}")

# client_app.run(main())



def export_task(config: ExportConfig):
        global API_ID
        API_ID = config.api_id
        global API_HASH
        API_HASH = config.api_hash
        global MEDIA_EXPORT
        MEDIA_EXPORT = {
            'audios': config.media_export_audios,
            'videos': config.media_export_videos,
            'photos': config.media_export_photos,
            'stickers': config.media_export_stickers,
            'animations': config.media_export_animations,
            'documents': config.media_export_documents,
            'voice_messages': config.media_export_voice_messages,
            'video_messages': config.media_export_video_messages,
            'contacts': config.media_export_contacts
        }
        global CHAT_EXPORT
        CHAT_EXPORT = {
            'contacts': config.chat_export_contacts,
            'bot_chats': config.chat_export_bot_chats,
            'personal_chats': config.chat_export_personal_chats,
            'public_channels': config.chat_export_public_channels,
            'public_groups': config.chat_export_public_groups,
            'private_channels': config.chat_export_private_channels,
            'private_groups': config.chat_export_private_groups
        }
        global CHAT_IDS
        CHAT_IDS = config.chat_ids
        global FILE_NOT_FOUND
        FILE_NOT_FOUND = '(File not included. Change data exporting settings to download.)'
        global JSON_FILE_PAGE_SIZE
        JSON_FILE_PAGE_SIZE = config.json_file_page_size

        global EXPORT_DATE_RANGE
        EXPORT_DATE_RANGE = config.export_date_range
        global EXPORT_FROM_DATE
        EXPORT_FROM_DATE = config.from_date
        global EXPORT_TO_DATE
        EXPORT_TO_DATE = config.to_date
        global SESSION_STRING
        SESSION_STRING = config.session_string

        global now 
        now = datetime.now()
        global range_type 
        range_type = EXPORT_DATE_RANGE.lower()
        global from_date, to_date

        if range_type == "week":
            from_date = now - timedelta(weeks=1)
            to_date = now
        elif range_type == "month":
            from_date = now - timedelta(weeks=4)
            to_date = now
        elif range_type == "year":
            from_date = now - timedelta(days=365)
            to_date = now
        elif range_type == "custom":
            from_date = datetime.strptime(EXPORT_FROM_DATE, "%Y-%m-%d")
            to_date = datetime.strptime(EXPORT_TO_DATE, "%Y-%m-%d") if EXPORT_TO_DATE else now
        elif range_type == "limited":
            # LIMIT = 10000
            CURRENT_CONFIG.messages_limit = 10000
            from_date = datetime.strptime("2013-08-14", "%Y-%m-%d")  # 2013-08-14
            to_date = datetime.now()
        else:
            from_date = datetime.strptime("2013-08-14", "%Y-%m-%d")  # 2013-08-14
            to_date = datetime.now()

        print(f"Export  range: {range_type}")
        print(f"Export date range: {from_date.strftime('%Y-%m-%d')} to {to_date.strftime('%Y-%m-%d')}")
        
        # "+79309686519"
        global client_app
        client_app = Client(
            name=str(CURRENT_CONFIG.base_dir / "app" / "db" / config.session_name),
            # name=config.session_name,
            api_id=API_ID,
            api_hash=API_HASH,
            session_string=config.session_string
        )

        client_app.run(main(config))

def run_export_in_process(config: ExportConfig):
    
    process = Process(target=export_task, args=(config,))
    process.start()