from telegram import Chat, ChatMember, ChatMemberUpdated, Update
from telegram.ext import Application


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