import os
import telegram
import logging
import httpx
import click
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from app.db_models import update_repair_status, Status

TG_TOKEN = os.environ["TOKEN"]
WORKING_CHAT = os.environ["CHAT"]

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.DEBUG
)
logger = logging.getLogger(__name__)

class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            instance = super().__call__(*args, **kwargs)
            cls._instances[cls] = instance
        return cls._instances[cls]

class CallbackHelper():
    def __init__(self):
        self.types = Status
        self.last_uuid = None
        self.last_status = None

    def check(self, callback_msg):
        parts = callback_msg.split(":")
        assert len(parts) == 2
        print(len(parts))
        print(self.types)
        print(parts[1] in self.types)
        condition = parts[1] in self.types and True # add uuid check
        self.last_status = parts[1] if condition else None
        self.last_uuid = parts[0] if condition else None
        print(self.last_status)
        print(self.last_uuid)
        return condition

    def handle_callback(self, callback_msg, master_id):
        if (self.check(callback_msg)):
            update_repair_status(self.last_uuid, self.last_status, master_id)


class TelegramBridge(metaclass=Singleton):
    def __init__(self, token, chat):
        self.app = Application.builder().token(token).build()
        self.app.add_handler(CallbackQueryHandler(self.get_button))
        self.app.add_handler(CommandHandler("upload", self.upload_spares))
        self.chat = chat
        self.callback_helper = CallbackHelper()

    def poll(self):
        self.app.run_polling(allowed_updates=Update.ALL_TYPES)

    async def send_message(self, message, **kwargs):
        await self.app.bot.send_message(chat_id=self.chat, text=message, parse_mode=telegram.constants.ParseMode.MARKDOWN_V2, reply_markup=kwargs.get("markup"))

    @staticmethod # делается сырым запросом чтобы бот мог получать апдейты в другом процессе
    async def send_new_order(order_form, order_uuid):
        msg_template = "Новый заказ от \[{soc_type}\] {contact}\n\nМодель {model}\n\n```{problem}```\n\nНомер заказа: `{uuid}`"
        httpx.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage", json={
            "chat_id":WORKING_CHAT,
            "text":msg_template.format(
            uuid=order_uuid, 
            soc_type=order_form.soc_type.value, 
            contact=order_form.contact, 
            model=order_form.model, 
            problem=order_form.problem
            ),
            "parse_mode":telegram.constants.ParseMode.MARKDOWN_V2,
            "reply_markup":{"inline_keyboard":[[{"text":"Принять","callback_data":f"{order_uuid}:{Status.ACCEPTED.value}"}]]}
        })

    async def get_button(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        query = update.callback_query
        await query.answer()

        self.callback_helper.handle_callback(query.data, query.from_user.id)
        await query.edit_message_text(text=f"Заказ `{self.callback_helper.last_uuid}` принят {query.from_user.first_name} {query.from_user.last_name if query.from_user.last_name else ''}",parse_mode=telegram.constants.ParseMode.MARKDOWN_V2)

    async def upload_spares(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        await update.message.reply_text(context)

@click.command("start-bot")
def start_bot_command():
    bot = TelegramBridge(TG_TOKEN, WORKING_CHAT)
    bot.poll()