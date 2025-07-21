# Both Telethon and Pyrogram should be Installed


import struct, base64
from telethon.sessions import StringSession
from telethon.sync import TelegramClient
from pyrogram.storage.storage import Storage
from telethon.crypto import AuthKey


def gramjs_to_unpack(sessionData):
    ST = StringSession("")
    ST.set_dc(sessionData["dc_id"], sessionData["serverAddress"], sessionData["port"])
    ST.auth_key = AuthKey(bytes.fromhex(sessionData["auth_key"]))
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


async def start_session(sessionData, api_id, api_hash):
    my_session = StringSession("")
    my_session.set_dc(sessionData["dc_id"], sessionData["serverAddress"], sessionData["port"])
    my_session.auth_key = AuthKey(bytes.fromhex(sessionData["auth_key"]))
    async with TelegramClient(
        my_session, api_id, api_hash,
        device_model='iPhone 15 Pro',
        system_version='iOS 17.5.1',
        app_version='Telegram iOS 10.8',
        lang_code='en',
        system_lang_code='en-US'
    ) as ses:
        ml = await ses.get_me()
    return ml


async def gramjs_to_pyro(sessionData, api_id, api_hash):
    DL = gramjs_to_unpack(sessionData)
    MK = await start_session(sessionData, api_id, api_hash)
    return pack_to_pyro(DL, MK, api_id)
