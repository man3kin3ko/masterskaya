from telegram import Chat, ChatMember, ChatMemberUpdated, Update, Bot
from telegram.ext import Application
import os

TG_TOKEN = os.environ["TOKEN"]


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            instance = super().__call__(*args, **kwargs)
            cls._instances[cls] = instance
        return cls._instances[cls]


class TelegramBridge(metaclass=Singleton):
    def __init__(self, token):
        self.app = Application.builder().token(token).build()

    def poll(self):
        self.app.run_polling()

    def send(self, msg):
        pass


bot = TelegramBridge(TG_TOKEN)


async def send_message_via_bot(bot_token, chat_id, message):
    bot = Bot(token=bot_token)
    await bot.send_message(chat_id=chat_id, text=message)
