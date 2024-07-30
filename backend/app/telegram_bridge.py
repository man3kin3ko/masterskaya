import os
import telegram
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from app.db_models import db

TG_TOKEN = os.environ["TOKEN"]
WORKING_CHAT = os.environ["CHAT"]

class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            instance = super().__call__(*args, **kwargs)
            cls._instances[cls] = instance
        return cls._instances[cls]


class TelegramBridge(metaclass=Singleton):
    def __init__(self, token, chat):
        self.app = Application.builder().token(token).build()
        self.app.add_handler(CallbackQueryHandler(self.get_button))
        self.app.add_handler(CommandHandler("upload", self.upload_spares))
        self.chat = chat

    def poll(self):
        self.app.run_polling(allowed_updates=Update.ALL_TYPES)

    async def send_message(self, message, **kwargs):
        await self.app.bot.send_message(chat_id=self.chat, text=message, parse_mode=telegram.constants.ParseMode.MARKDOWN_V2, reply_markup=kwargs.get("markup"))

    async def send_new_order(self, order_form, new_order_uuid):
        msg_template = "Новый заказ от \[{soc_type}\] {contact}\n\nМодель {model}\n\n```{problem}```\n\nНомер заказа: `{uuid}`"
        await self.send_message(msg_template.format(
            uuid=new_order_uuid, 
            soc_type=order_form.soc_type.value, 
            contact=order_form.contact, 
            model=order_form.model, 
            problem=order_form.problem
            ), markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("Принять заказ", callback_data="accept_repair")]]
                ))

    async def get_button(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        query = update.callback_query
        await query.answer()

        await query.edit_message_text(text=f"Selected option: {query.data}")

        # if callback == accept repar db.add(master) + change status

    async def upload_spares(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        await update.message.reply_text(context)

bot = TelegramBridge(TG_TOKEN, WORKING_CHAT)