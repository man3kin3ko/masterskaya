import os
import telegram
import httpx
import click
from .utils import truncate
from typing import Tuple
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from .db_models import (
    update_repair_status, 
    get_categ, 
    export_csv, 
    Status,
    SpareType, 
    get_order_page, 
    get_categs_page, 
    get_repair_order_full
    )

TG_TOKEN = os.environ["TOKEN"]
WORKING_CHAT = os.environ["CHAT"]

class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            instance = super().__call__(*args, **kwargs)
            cls._instances[cls] = instance
        return cls._instances[cls]


class InlineKeyboardUI(): # наследование от маркапа невозможно, тк там переопределен сетаттр(
    def __init__(self, rows):
        self.rows = rows
        self.route = None

    def from_route(self, route):
        self.route = route
        self.page = 1
        return self

    def set_route(self, route):
        self.route = route.lstrip("/").split("/")
        if (len(self.route) > 2):
            self.page = int(self.route[2])

    def create(self):
        return InlineKeyboardMarkup(self.rows)

    def next(self):
        return f"/{self.route[0]}/page/{self.page + 1}"

    def back(self):
        return f"/{self.route[0]}/page/{self.page - 1 if self.page > 1 else 1}"


class InlineKeyboardUIBuilder:
    def __init__(self, max_per_page=5):
        self.max_per_page = max_per_page
        self.reset()
        self._menu_btn = InlineKeyboardButton(text="Меню", callback_data="/menu")

    def reset(self) -> None:
        self._product = InlineKeyboardUI([])

    def init(self, product):
        self._product = product

    @property
    def product(self) -> InlineKeyboardUI:
        print(self._product.rows[0])
        assert len(self._product.rows[0]) <= self.max_per_page + 1
        product = self._product.create()
        self.reset()
        return product
    
    def add_button(self, text, callback):
        self.add_row([InlineKeyboardButton(text=text, callback_data=callback)])

    def add_row(self, row):
        self._product.rows.append(row)

    def add_route(self, route):
        self._product.set_route(route)

    def add_menu_btn(self):
        self._product.rows.append([self._menu_btn])

    def add_back_btn(self):
        self._product.rows.append([InlineKeyboardButton(text="⬅️", callback_data=self._product.back())])

    def add_pager(self):
        self._product.rows.append(
            [
                InlineKeyboardButton(text="⬅️", callback_data=self._product.back()),
                self._menu_btn,
                InlineKeyboardButton(text="➡️", callback_data=self._product.next()),
            ]
        )
    
    def make_menu(self):
        self.add_route("/menu")
        self.add_row(
                [InlineKeyboardButton(text="Мои заказы", callback_data=f"/order/page/1")]
            )
        self.add_row(
                [InlineKeyboardButton(text="Запчасти", callback_data=f"/spares/page/1")]
            )

    def add_status_switch(self, uuid, current_status):
        row  = [i for i in Status if i.name != current_status.name and i.name != Status.ORDERED.name]
        self.add_row(list(map(lambda i: InlineKeyboardButton(text=str(i), callback_data=f"/order/{uuid}/{i.value}"), row)))
        
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
        self.add_menu_btn()

    def add_file_toggle(self, categ_id):
        self.add_row([
            InlineKeyboardButton(
                text="Скачать",  
                callback_data=f"/spares/{categ_id}/download",
                ),
            InlineKeyboardButton(
                text="Загрузить",  
                callback_data=f"/spares/{categ_id}/uplosad",
                ),
        ])


class CallbackRouter:
    def __init__(self, builder, desc_len=20):
        self.statuses = Status
        self.builder = builder
        self.desc_len = desc_len

    def update_order(self, uuid, status, master):
        update_repair_status(uuid, status, master.id)
        return f"Заказ `{uuid}` изменен {master.first_name} {master.last_name if master.last_name else ''} на `{str(Status(status))}`", None

    def get_orders(self, page, master):
        self.builder.add_route(f"/order/page/{page}")
        for uniq_link, desc, model in get_order_page(self.builder.max_per_page, page, master.id):
            self.builder.add_button(text=f"{model} {truncate(desc, self.desc_len)}", callback=f"/order/{uniq_link}/item")
        self.builder.add_pager()
        return "Меню", self.builder.product
    
    def get_spare(self, categ_id, route):
        prev = InlineKeyboardUI([])
        self.builder.init(prev.from_route(route))
        self.builder.add_file_toggle(categ_id)
        self.builder.add_back_btn()
        return f"{get_categ(categ_id)[0]}", self.builder.product

    def get_order(self, uuid, route):
        model, status, date, desc, soc_type, contact = get_repair_order_full(uuid)
        prev = InlineKeyboardUI([])
        self.builder.init(prev.from_route(route))
        self.builder.add_status_switch(uuid, status)
        self.builder.add_back_btn()
        msg = 'Заказ `{uuid}` от `{date}`:\n{model} \[{soc_type}\] {contact}\n```{desc}```\nСтатус: {status}'.format(
            uuid=uuid,
            model=model,
            date=date.date(),
            status=str(status),
            desc=desc,
            soc_type=soc_type.value,
            contact=contact
        )
        return msg, self.builder.product

    def get_categ(self, page):
        self.builder.add_route(f"/spares/page/{page}")
        for categ_id, name in get_categs_page(self.builder.max_per_page, page):
            self.builder.add_button(text=f"{name}", callback=f"/spares/{categ_id}/item")
        self.builder.add_pager()
        return "Меню", self.builder.product

    def handle_callback(self, callback_msg, master) -> Tuple[str, InlineKeyboardUI]:
        route = callback_msg.lstrip("/").split("/")
        if (route[0] == "menu"):
            self.builder.make_menu()
            return "Меню", self.builder.product
            
        elif (route[0] == "order"):
            if route[1] == "page":
                return self.get_orders(route[2], master)
            if route[2] in self.statuses:
                return self.update_order(route[1], route[2], master)
            if route[2] == "item":
                return self.get_order(route[1], route)
                
        elif (route[0] == "spares"):
            if len(route) < 3:
                return "Меню", self.builder.make_spares()
            if route[1] == "page":
                return self.get_categ(route[2])
            if route[2] == 'item':
                return self.get_spare(route[1], route)
            if route[2] == 'download':
                export_csv(route[1])
                return None, None
            if route[2] == 'upload':
                    #https://stackoverflow.com/questions/31394998/using-sqlalchemy-to-load-a-csv-file-into-a-database
                pass
        return f"```{route} {Status(route[2]) in self.statuses} {self.statuses} {Status.ACCEPTED.value}```", None


class TelegramBridge(metaclass=Singleton):
    def __init__(self, token, chat):
        self.app = Application.builder().token(token).updater(None).build()
        self.app.add_handler(CallbackQueryHandler(self.get_button))
        self.app.add_handler(CommandHandler("menu", self.menu))
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

    async def send_new_order(self, order_form, order_uuid):
        msg_template = "Новый заказ от \[{soc_type}\] {contact}\n\nМодель {model}\n\n```{problem}```\n\nНомер заказа: `{uuid}`"
        await self.send_message(msg_template.format(
            uuid=order_uuid, 
            soc_type=order_form.soc_type.value, 
            contact=order_form.contact, 
            model=order_form.model, 
            problem=order_form.problem
            ), markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("Принять заказ", callback_data="accept_repair")]]
                ))

    async def get_button(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()

        text, kb = self.router.handle_callback(query.data, query.from_user)
        print(text)
        if text is not None:
            await query.edit_message_text(
                text=text,
                parse_mode=telegram.constants.ParseMode.MARKDOWN_V2,
            )
        if kb is not None:
            print(kb)
            await query.edit_message_reply_markup(reply_markup=kb)
        if text is None and kb is None:
            print(query.to_dict()['message']['reply_markup']['inline_keyboard'])
            await self.app.bot.send_document(self.chat, open('temp.csv', 'rb'))

    async def menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        self.builder.make_menu()
        await self.send_message(message=f"Меню", markup=self.builder.product)


@click.command("start-bot")
def start_bot_command():
    bot = TelegramBridge(TG_TOKEN, WORKING_CHAT)
    bot.poll()
