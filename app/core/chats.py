from pyrogram import Client
from pyrogram.enums import ChatType
# from configs import CHAT_EXPORT
from app.core.state import CURRENT_CONFIG

CHAT_EXPORT = {'public_channels':CURRENT_CONFIG.chat_export_public_channels,
               'public_groups':CURRENT_CONFIG.chat_export_public_groups,
               'personal_chats':CURRENT_CONFIG.chat_export_personal_chats,
               'bot_chats':CURRENT_CONFIG.chat_export_bot_chats}

class Chat:
    def __init__(self, app: Client):
        self.app = app
        # self.chat_type_counters = chat_type_counters

    async def get_ids(self, private = True, last_message_date = None) -> list:
        dialog_ids = []
        async for dialog in self.app.get_dialogs():
            # print(dialog)
            # if dialog.top_message.date and last_message_date:
            #     if dialog.top_message.date < last_message_date:
            #         continue
            # TODO: private channel
            # but this is for all channels
            if CHAT_EXPORT['public_channels'] is True: 
                if dialog.chat.type == ChatType.CHANNEL:
                    dialog_ids.append(dialog.chat.id)
                    # self.chat_type_counters['public_channels'] += 1
        
            # TODO: but this is for all groups
            # TODO: for SUPERGROUP?
            # TODO: private groups
            if CHAT_EXPORT['public_groups'] is True:
                if dialog.chat.type == ChatType.GROUP:
                    dialog_ids.append(dialog.chat.id)
                    # self.chat_type_counters['public_groups'] += 1

            if CHAT_EXPORT['personal_chats'] is True: 
                if dialog.chat.type == ChatType.PRIVATE:
                    dialog_ids.append(dialog.chat.id)
                    # self.chat_type_counters['personal_chats'] += 1
            
            if CHAT_EXPORT['bot_chats'] is True: 
                if dialog.chat.type == ChatType.BOT:
                    dialog_ids.append(dialog.chat.id)

        return dialog_ids

