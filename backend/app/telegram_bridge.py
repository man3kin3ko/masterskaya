import os
import telegram
import logging
import httpx
import click
from typing import Tuple
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from app.db_models import update_repair_status, Status, SpareType, get_order_page

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


class InlineKeyboardUI(InlineKeyboardMarkup):
    def __init__(self, rows):
        self.rows = rows

    def create(self):
        super().__init__(self.rows)

    def next(self):
        pass

    def back(self):
        pass


class InlineKeyboardUIBuilder:
    def __init__(self, max_per_page=5):
        self.max_per_page = max_per_page
        self.reset()
        self._back_btn = InlineKeyboardButton(text="Меню", callback_data="/menu")

    def reset(self) -> None:
        self._product = InlineKeyboardUI([])

    @property
    def product(self) -> InlineKeyboardUI:
        product = self._product.create()
        self.reset()
        return product
    
    def add_button(self, text, callback):
        self.add_row(InlineKeyboardButton(text=text, callback_data=callback))

    def add_row(self, row):
        self._product.rows.append(row)

    def add_route(self, route):
        self._product.route = route

    def add_back_btn(self):
        self._product.rows.append([self._back_btn])

    def add_pager(self):
        self.product.rows.append(
            [
                InlineKeyboardButton(text="⬅️", callback_data=self.product.back()),
                self._back_btn,
                InlineKeyboardButton(text="⬅️", callback_data=self.product.next()),
            ]
        )
    
    def make_menu(self):
        self.add_route("/menu")
        self.add_row(
                [InlineKeyboardButton(text="Мои заказы", callback_data=f"/order")]
            )
        self.add_row(
                [InlineKeyboardButton(text="Запчасти", callback_data=f"/spares")]
            )
        
    def make_spares(self):
        self.add_route(f"/spares/")
        self.add_row(
                    [
                        InlineKeyboardButton(
                            text="Электроника",
                            callback_data=f"/spares/{SpareType.ELECTRIC.value}",
                        )
                    ]
                )
        self.add_row(
                    [
                        InlineKeyboardButton(
                            text="Механика",
                            callback_data=f"/spares/{SpareType.MECHA.value}",
                        )
                    ]
                )
        self.add_back_btn()


class CallbackRouter:
    def __init__(self, builder):
        self.statuses = Status
        self.builder = builder

    def update_order(self, uuid, status, master):
        update_repair_status(uuid, status, master.id)
        return f"Заказ `{uuid}` принят {master.first_name} {master.last_name if master.last_name else ''}"

    def get_orders(self, page, master):
        self.builder.add_route(f"/order/page/{page}")
        for i in get_order_page(page, self.builder.max_per_page, master.id):
            print(i)
            desc = "sdsdsd...."
            self.builder.add_button(text=f"{i.model} {desc}", callback=i.uniq_link)
        self.builder.add_pager()
        return None, self.builder.product
    
    def get_spares(self, page):
        pass

    def get_order(self):
        pass

    def get_categ(self):
        pass

    def handle_callback(self, callback_msg, master) -> Tuple[str, InlineKeyboardUI]:
        route = callback_msg.split("/")
        match route[0]:
            case "menu":
                return None, self.builder.make_menu()
            
            case "order":
                if route[1] == "page":
                    return self.get_orders(route[2], master)
                if route[2] in self.statuses:
                    return self.update_order(route[1], route[2], master)
                if route[2] == "item":
                    return self.get_order(route[1])
                
            case "spares":
                if len(route) < 3:
                    return None, self.builder.make_spares()
                if route[1] == "page":
                    return self.get_spares(route[2], master)
                if route[2] == 'item':
                    return self.get_categ(route[1])
            
            case _:
                return f"Probably an error occured.\n ```{callback_msg}```", None


class TelegramBridge(metaclass=Singleton):
    def __init__(self, token, chat):
        self.app = Application.builder().token(token).build()
        self.app.add_handler(CallbackQueryHandler(self.get_button))
        self.app.add_handler(CommandHandler(["help", "menu"], self.menu))
        self.chat = chat
        self.builder = InlineKeyboardUIBuilder()
        self.router = CallbackRouter(self.builder)

    def poll(self):
        self.app.run_polling(allowed_updates=Update.ALL_TYPES)

    async def send_message(self, message, **kwargs):
        await self.app.bot.send_message(
            chat_id=self.chat,
            text=message,
            parse_mode=telegram.constants.ParseMode.MARKDOWN_V2,
            reply_markup=kwargs.get("markup"),
        )

    @staticmethod  # делается сырым запросом чтобы бот мог получать апдейты в другом процессе. таков костыль(
    async def send_new_order(order_form, order_uuid):
        msg_template = "Новый заказ от \[{soc_type}\] {contact}\n\nМодель {model}\n\n```{problem}```\n\nНомер заказа: `{uuid}`"
        httpx.post(
            f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
            json={
                "chat_id": WORKING_CHAT,
                "text": msg_template.format(
                    uuid=order_uuid,
                    soc_type=order_form.soc_type.value,
                    contact=order_form.contact,
                    model=order_form.model,
                    problem=order_form.problem,
                ),
                "parse_mode": telegram.constants.ParseMode.MARKDOWN_V2,
                "reply_markup": {
                    "inline_keyboard": [
                        [
                            {
                                "text": "Принять",
                                "callback_data": f"/order/{order_uuid}/{Status.ACCEPTED.value}",
                            }
                        ]
                    ]
                },
            },
        )

    async def get_button(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()

        text, kb = self.router.handle_callback(query.data, query.from_user)
        if text is not None:
            await query.edit_message_text(
                text=text,
                parse_mode=telegram.constants.ParseMode.MARKDOWN_V2,
            )
        if kb is not None:
            await query.update_reply_markup(reply_markup=kb)

    async def menu(self):
        self.send_message(message="test", markup=self.builder.make_menu())


@click.command("start-bot")
def start_bot_command():
    bot = TelegramBridge(TG_TOKEN, WORKING_CHAT)
    bot.poll()
