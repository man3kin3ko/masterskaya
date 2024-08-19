import os
import telegram
import httpx
import click
import logging
from .utils import truncate, Singleton
from typing import Tuple
from dataclasses import dataclass
from telegram.ext import (
    ExtBot,
    Application, 
    CallbackQueryHandler, 
    CommandHandler, 
    TypeHandler,
    ContextTypes,
    CallbackContext
    )
from telegram import (
    InlineKeyboardButton, 
    InlineKeyboardMarkup, 
    Update
    )
from .db import db_proxy, Status

TG_TOKEN = os.environ["TOKEN"]
WORKING_CHAT = os.environ["CHAT"]

@dataclass
class FlaskUpdate:
    user_id: int
    payload: str

class CustomContext(CallbackContext[ExtBot, dict, dict, dict]):
    @classmethod
    def from_update(
        cls,
        update: object,
        application: "Application",
    ) -> "CustomContext":
        if isinstance(update, FlaskUpdate):
            return cls(application=application, user_id=update.user_id)
        return super().from_update(update, application)


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
    def __init__(self, max_per_page):
        self.max_per_page = max_per_page
        self.reset()
        self._menu_btn = InlineKeyboardButton(text="Меню", callback_data="/menu")

    def reset(self) -> None:
        self._product = InlineKeyboardUI([])

    def init(self, product):
        self._product = product

    @property
    def product(self) -> InlineKeyboardUI:
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

    def add_status_switch(self, uuid, current_status: Status):
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
                callback_data=f"/spares/{categ_id}/upload",
                ),
        ])


class CallbackRouter:
    def __init__(self, builder, db_proxy, desc_len=20):
        self.statuses = Status
        self.builder = builder
        self.db_proxy = db_proxy
        self.desc_len = desc_len

    def update_order(self, uuid, status, master):
        order = db_proxy.get_repair_order(uuid, master)[0]
        return order.update(status, master), None

    def get_orders_page(self, page, master):
        self.builder.add_route(f"/order/page/{page}")
        page = self.db_proxy.get_repair_orders(master.id, page)
        for i in page.items:
            self.builder.add_button(text=f"{i.model} {truncate(i.problem, self.desc_len)}", callback=f"/order/{i.uniq_link}/item")
        self.builder.add_pager()
        return "Меню", self.builder.product
    
    def get_category(self, categ_id, route):
        prev = InlineKeyboardUI([])
        self.builder.init(prev.from_route(route))
        self.builder.add_file_toggle(categ_id)
        self.builder.add_back_btn()

        categ = db_proxy.get_category_by_id(categ_id)[0]
        logging.debug(categ)

        return str(categ), self.builder.product

    def get_order(self, uuid, route):
        order = db_proxy.get_repair_order(uuid)[0]
        prev = InlineKeyboardUI([])
        self.builder.init(prev.from_route(route))
        self.builder.add_status_switch(uuid, order.status)
        self.builder.add_back_btn()

        msg = '\n'.join([
            order.get_title(),
            order.get_description(),
            order.get_status(),
            "\n",
            order.get_tracking_link(),
            order.get_created_time(),
        ])

        return msg, self.builder.product

    def get_categories_page(self, page):
        self.builder.add_route(f"/spares/page/{page}")
        page = db_proxy.get_categories_page(self.builder.max_per_page, page)
        for i in page.items:
            self.builder.add_button(text=f"{i.name}", callback=f"/spares/{i.id}/item")
        self.builder.add_pager()
        return "Меню", self.builder.product

    def handle_callback(self, callback_msg, master) -> Tuple[str, InlineKeyboardUI]:
        route = callback_msg.lstrip("/").split("/")
        if (route[0] == "menu"):
            self.builder.make_menu()
            return "Меню", self.builder.product
            
        elif (route[0] == "order"):
            if route[1] == "page":
                return self.get_orders_page(route[2], master)
            if route[2] in self.statuses:
                return self.update_order(route[1], route[2], master)
            if route[2] == "item":
                return self.get_order(route[1], route)
                
        elif (route[0] == "spares"):
            if len(route) < 3:
                return "Меню", self.builder.make_spares()
            if route[1] == "page":
                return self.get_categories_page(route[2])
            if route[2] == 'item':
                return self.get_category(route[1], route)
            if route[2] == 'download':
                export_csv(route[1])
                return None, None
            if route[2] == 'upload':
                    #https://stackoverflow.com/questions/31394998/using-sqlalchemy-to-load-a-csv-file-into-a-database
                pass
        return f"```{route}```", None


class TelegramBridge(metaclass=Singleton):
    def __init__(self, token, chat, flask, max_page_size=5):
        self.app = Application.builder().token(token).build()
        self.app.add_handler(CallbackQueryHandler(self.get_button))
        self.app.add_handler(CommandHandler("menu", self.menu))
        self.app.add_handler(TypeHandler(type=FlaskUpdate, callback=self.send_new_order))

        self.chat = chat
        self.builder = InlineKeyboardUIBuilder(max_page_size)
        self.router = CallbackRouter(self.builder, db_proxy)

    async def add_update(self, update):
        await self.app.update_queue.put(FlaskUpdate(user_id=self.chat, payload=update))

    async def send_message(self, message, **kwargs):
        await self.app.bot.send_message(
            chat_id=self.chat,
            text=message,
            parse_mode=telegram.constants.ParseMode.MARKDOWN_V2,
            reply_markup=kwargs.get("markup"),
        )

    async def send_new_order(self, update: FlaskUpdate, context: CustomContext):
        uniq_link = update.payload
        order = db_proxy.get_order(uniq_link)[0]
        await self.send_message(str(order), markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("Принять заказ", callback_data=f"/order/{uniq_link}/{Status.ACCEPTED.value}")]]
                ))

    async def get_button(self, update: Update, context: CustomContext):
        query = update.callback_query
        await query.answer()

        text, kb = self.router.handle_callback(query.data, query.from_user)

        if text is not None:
            await query.edit_message_text(
                text=text,
                parse_mode=telegram.constants.ParseMode.MARKDOWN_V2,
            )
        if kb is not None:
            await query.edit_message_reply_markup(reply_markup=kb)

    async def menu(self, update: Update, context: CustomContext):
        self.builder.make_menu()
        await self.send_message(message=f"Меню", markup=self.builder.product)

def start_bot(app):
    return TelegramBridge(TG_TOKEN, WORKING_CHAT, app)

@click.command("start-bot")
def start_bot_command():
    bot = TelegramBridge(TG_TOKEN, WORKING_CHAT)
    bot.poll()
