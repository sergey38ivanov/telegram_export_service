# Both Telethon and Pyrogram should be Installed

import struct, base64
from telethon.sessions.string import StringSession
from telethon.sync import TelegramClient
from pyrogram.storage.storage import Storage


def telethon_to_unpack(string):
    ST = StringSession(string)
    return ST


def pack_to_pyro(data, ses, api_id):
    Dt = Storage.SESSION_STRING_FORMAT
    return (
        base64.urlsafe_b64encode(
            struct.pack(Dt, data.dc_id, api_id, None, data.auth_key.key, ses.id, ses.bot)
        )
        .decode()
        .rstrip("=")
    )


async def start_session(string, api_id, api_hash):
    async with TelegramClient(
        StringSession(string), api_id, api_hash,
        device_model='EroticBot',
        system_version='EroOS 6.9',
        app_version='69.420',
        lang_code='en',
        system_lang_code='en-US'
    ) as ses:
        ml = await ses.get_me()
    return ml


async def tele_to_pyro(string, api_id, api_hash):
    DL = telethon_to_unpack(string)
    MK = await start_session(string, api_id, api_hash)
    return pack_to_pyro(DL, MK, api_id)
