import os
import abc
import csv
import httpx
import click
import logging
from dataclasses import dataclass

import telegram
import telegram.ext.filters as filters
from telegram import Update
from telegram.ext import (
    ExtBot,
    Application, 
    CallbackQueryHandler, 
    ConversationHandler,
    CommandHandler, 
    TypeHandler,
    ContextTypes,
    CallbackContext,
    MessageHandler,
    )

from .ui import InlineKeyboardUI, InlineKeyboardUIBuilder
from ..utils import truncate, Singleton, async_to_sync
from ..db import db_proxy, SpareUpdate, Status

TG_TOKEN = os.environ["TOKEN"]
WORKING_CHAT = os.environ["CHAT"]

logging.getLogger("httpx").setLevel(logging.WARNING)

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
        if route[1] == "page" or route[2] == "page":
            return self.handle_page(route)
        if route[-1] == "item":
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
        def wrapper(self, *args):
            another_handler = self.handle_pass(args[0])
            if another_handler is None:
                return f(self, *args)
            return another_handler
        return wrapper

    @staticmethod
    def can_parent_handle(f):
        def wrapper(self, *args):
            upcasted = super(type(self), self)
            parent_handling = upcasted.handle(args[0])
            if parent_handling is None:
                return f(self, *args)
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
        order = db_proxy.get_repair_order(uuid, self.master)

        return order.update(status, self.master), None

    def handle_item(self, route):
        uuid = route[1]
        order = db_proxy.get_repair_order(uuid)
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
        page = db_proxy.get_order_page(page_num, self.master.id)

        for i in page.items:
            self.builder.add_button(
                text=f"{i.model} {truncate(i.problem, self.desc_len)}", 
                callback=f"/{self.prog_name}/{i.uniq_link}/item"
                )
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
        categ = db_proxy.get_category_by_id(categ_id)
        prev = InlineKeyboardUI([])
        self.builder.init(prev.from_route(route))
        self.builder.add_file_toggle(categ_id)
        self.builder.add_back_btn()

        return str(categ), self.builder.product

    def handle_page(self, route):
        page_num = self.get_page(route)
        page = db_proxy.get_categories_page(page_num)

        for i in page.items:
            self.builder.add_button(
                text=f"{i.name}", 
                callback=f"/{self.prog_name}/{i.id}/item"
                )
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

    WAIT_FOR_UPDATE = 1

    def __init__(self, token, chat, flask, max_page_size=5):
        self.app = Application.builder().token(token).build()
        self.updated_spares_id = None
        self.app.add_handler(ConversationHandler(
            entry_points=[CallbackQueryHandler(get_ready_for_update, pattern="^\/spares\/\d+\/upload/$")],
            states={
                WAIT_FOR_UPDATE:[MessageHandler(filters.ATTACHMENT, wait_for_update)]
            },
            fallbacks=[CallbackQueryHandler(reset_state, pattern="^reset$")]
        ))
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

    async def reset_state(self, update, context):
        self.updated_spares_id = None

        return ConversationHandler.END

    async def get_ready_for_update(self, update, context):
        query = update.callback_query
        await query.answer()
        
        self.updated_spares_id = self.router.make_route(query.data)[1]
        return self.WAIT_FOR_UPDATE

    async def wait_for_update(self, update, context):
        try:
            document_update = SpareUpdate(
                await update.message.document.get_file(), 
                update.message.document.file_name
                )
            await document_update.download()
            document_update.parse()
            document_update.delete()
            self.updated_spares_id = None

            return ConversationHandler.END

        except Exception as e:
            self.builder.add_button("⬅️", "reset")
            await self.send_message(
                f"Произошла ошибка\n```{e.__repr__()}```.\n Попробуйте снова"б
                markup=self.builder.product
                )
            return self.WAIT_FOR_UPDATE

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
        uniq_link = update.payload #validate?
        order = db_proxy.get_order(uniq_link)
        self.builder.accept_order(uniq_link)
        await self.send_message(str(order), markup=self.builder.product)

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
