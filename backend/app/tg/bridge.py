import os
import abc
import csv
import telegram
import httpx
import click
import logging
from .ui import InlineKeyboardUI, InlineKeyboardUIBuilder
from ..utils import truncate, Singleton, async_to_sync
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
from ..db import db_proxy, Status

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

class AbstractHandler():
    __metaclass__ = abc.ABCMeta

    _next_handler = None

    def set_next(self, handler):
        self._next_handler = handler
        return handler

    def handle(self, route):
        if route[1] == "page":
            return self.handle_page(route)
        if route[2] == "item":
            return self.handle_item(route)

    def handle_pass(self, route):
        if not (route[0] == self.prog_name):
            return self.handle_next(route)

    def get_page(self, route):
        page_num = int(route[2])
        self.builder.add_route(f"/{self.prog_name}/page/{page_num}")
        return page_num

    @abc.abstractmethod
    def handle_next(self, route):
        if self._next_handler:
            return self._next_handler.handle(route)

    @abc.abstractmethod
    def handle_page(self, route):
        pass

    @abc.abstractmethod
    def handle_item(self, route):
        pass

    @staticmethod
    def is_this_handler(f):
        def wrapper(*args):
            it = args[0]
            another_handler = it.handle_pass(args[1])
            if another_handler is None:
                return f(*args)
            return another_handler
        return wrapper

    @staticmethod
    def can_parent_handle(f):
        def wrapper(*args):
            it = args[0]
            upcasted = super(type(it), it)
            parent_handling = upcasted.handle(args[1])
            if parent_handling is None:
                return f(*args)
            return parent_handling
        return wrapper

class MenuHandler(AbstractHandler):
    def __init__(self, builder):
        self.builder = builder
        self.prog_name = "menu"

    @AbstractHandler.is_this_handler
    def handle(self, route):
        self.builder.make_menu()
        return "Меню", self.builder.product

class OrderHandler(AbstractHandler):
    def __init__(self, builder, master, desc_len=20):
        self.prog_name = "order"
        self.builder = builder
        self.statuses = Status
        self.master = master
        self.desc_len = desc_len

    @AbstractHandler.is_this_handler
    @AbstractHandler.can_parent_handle
    def handle(self, route):
        if route[2] in self.statuses:
            return self.handle_update(route)

    def handle_update(self, route):
        uuid = route[1]
        status = route[2]
        order = db_proxy.get_repair_order(uuid, self.master)[0]

        return order.update(status, self.master), None

    def handle_item(self, route):
        uuid = route[1]
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

    def handle_page(self, route):
        page_num = self.get_page(route)
        page = db_proxy.get_repair_orders(self.master.id, page_num)

        for i in page.items:
            self.builder.add_button(text=f"{i.model} {truncate(i.problem, self.desc_len)}", callback=f"/{self.prog_name}/{i.uniq_link}/item")
        self.builder.add_pager()

        return "Меню", self.builder.product
            

class SpareHandler(AbstractHandler):
    def __init__(self, builder, callback):
        self.builder = builder
        self.callback = callback
        self.prog_name = "spares"
    
    @AbstractHandler.is_this_handler
    @AbstractHandler.can_parent_handle
    def handle(self, route):
        if route[2] == 'download':
            self.callback(self.handle_download(route))
            return None, None

    def handle_item(self, route):
        categ_id = route[1]
        categ = db_proxy.get_category_by_id(categ_id)[0]
        prev = InlineKeyboardUI([])
        self.builder.init(prev.from_route(route))
        self.builder.add_file_toggle(categ_id)
        self.builder.add_back_btn()

        return str(categ), self.builder.product

    def handle_page(self, route):
        page_num = self.get_page(route)
        page = db_proxy.get_categories_page(self.builder.max_per_page, page_num)

        for i in page.items:
            self.builder.add_button(text=f"{i.name}", callback=f"/{self.prog_name}/{i.id}/item")
        self.builder.add_pager()

        return "Меню", self.builder.product

    def handle_download(self, route):
        category_name, header, lines = db_proxy.export_category_to_csv(route[1])
        filename = f"instance/{category_name}.csv"

        with open(filename, 'w') as f:
            writer = csv.writer(f)
            writer.writerow(header)
            for line in lines:
                writer.writerow(line)
        
        return filename

class CallbackRouter:
    def __init__(self, msg_callback, kb_callback, doc_callback, max_page_size):
        self.max_page_size = max_page_size
        self.msg_callback = async_to_sync(msg_callback)
        self.kb_callback = async_to_sync(kb_callback)
        self.doc_callback = async_to_sync(doc_callback)

    @staticmethod
    def make_route(msg):
        route = msg.lstrip("/").split("/")
        while len(route) < 3:
            route.append(None)
        return route

    def make_callback(self, query, msg, kb):
        if msg is not None:
            self.msg_callback(query, msg)
        if kb is not None:
            self.kb_callback(query, kb)

    def handle_callback(self, query):
        callback_msg = query.data
        master = query.from_user
        route = self.make_route(callback_msg)
        builder = InlineKeyboardUIBuilder(self.max_page_size)
        menu = MenuHandler(builder=builder)
        order = OrderHandler(builder=builder, master=master)
        spare = SpareHandler(builder=builder, callback=self.doc_callback)
        
        menu.set_next(order).set_next(spare)
        self.make_callback(query, *menu.handle(route))


class TelegramBridge(metaclass=Singleton):
    def __init__(self, token, chat, flask, max_page_size=5):
        self.app = Application.builder().token(token).build()
        self.app.add_handler(CallbackQueryHandler(self.get_button))
        self.app.add_handler(CommandHandler("menu", self.menu))
        self.app.add_handler(TypeHandler(type=FlaskUpdate, callback=self.send_new_order))

        self.chat = chat
        self.builder = InlineKeyboardUIBuilder(max_page_size)
        self.router = CallbackRouter(
            self.edit_text,
            self.edit_kb,
            self.send_document,
            max_page_size
            )

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

    async def send_document(self, path):
        await self.app.bot.send_document(chat_id=self.chat, document=open(path, 'rb'))

    async def edit_kb(self, query, kb):
        await query.edit_message_reply_markup(reply_markup=kb)

    async def edit_text(self, query, msg):
        await query.edit_message_text(
                text=msg,
                parse_mode=telegram.constants.ParseMode.MARKDOWN_V2,
            )

    async def get_button(self, update: Update, context: CustomContext):
        query = update.callback_query
        await query.answer()

        self.router.handle_callback(query)

    async def menu(self, update: Update, context: CustomContext):
        self.builder.make_menu()
        await self.send_message(message=f"Меню", markup=self.builder.product)

def start_bot(app):
    return TelegramBridge(TG_TOKEN, WORKING_CHAT, app)

@click.command("start-bot")
def start_bot_command():
    bot = TelegramBridge(TG_TOKEN, WORKING_CHAT)
    bot.poll()
