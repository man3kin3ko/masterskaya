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

from .ui import InlineKeyboardUI, InlineKeyboardUIBuilder, Routes
from ..utils import truncate, Singleton, async_to_sync, is_class
from ..db import db_proxy, SpareUpdate, Status

TG_TOKEN = os.environ["TOKEN"]
WORKING_CHAT = os.environ["CHAT"]

logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


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


class AbstractHandler:
    __metaclass__ = abc.ABCMeta

    WAIT_FOR_UPDATE = -1

    @staticmethod
    def make_route(query):
        return query.data.strip("/").split("/")

    @staticmethod
    def get_master(query):
        return query.from_user

    def init_builder(self, route):
        kb = InlineKeyboardUI([])
        self.builder.init(kb.from_route(route))

    def _get_page(self, route):
        if len(route) > 1:
            return route[self.PAGE_NUM]
        return 1

    async def parse_update(self, update):
        query = await self.catch_update(update)
        route = self.make_route(query)
        return query, route

    async def catch_update(self, update):
        query = update.callback_query
        await query.answer()

        return query

    async def answer(self, query, text, kb=None):
        await self.bridge.edit_text(query, text)
        if kb is not None:
            await self.bridge.edit_kb(query, kb)


class AdminHandler(AbstractHandler):
    def __init__(self, bridge):
        self.bridge = bridge
        self.builder = bridge.builder

        # bridge.app.add_handler(
        #     CommandHandler("trace", callback=self.send_traceback)
        # )

    def _authorize(self):
        return True

    async def send_traceback(self, update, context):
        if self._authorize():
            logger.debug(update)
            os._exit(1)


class MenuHandler(AbstractHandler):
    def __init__(self, bridge):
        self.bridge = bridge
        self.builder = bridge.builder
        bridge.app.add_handler(CallbackQueryHandler(self.send_menu, pattern=Routes.menu))
        bridge.app.add_handler(CommandHandler("menu", self.send_menu))

    async def send_menu(self, update: Update, context: CustomContext):
        self.builder.make_menu()
        await self.bridge.send_message(message=f"Меню", markup=self.builder.product)


class OrderHandler(AbstractHandler):

    UUID = 1
    STATUS = 2
    PAGE_NUM = 1
    DESC_LEN = 10

    def __init__(self, bridge):
        self.bridge = bridge
        self.builder = bridge.builder
        bridge.app.add_handler(
            CallbackQueryHandler(self.handle_page, pattern=Routes.orders)
        )
        bridge.app.add_handler(
            CallbackQueryHandler(self.handle_item, pattern=Routes.order)
        )
        bridge.app.add_handler(
            CallbackQueryHandler(self.change_item, pattern=Routes.order_change)
        )

    async def change_item(self, update, context):
        query, route = await self.parse_update(update)
        uuid = route[self.UUID]
        status = route[self.STATUS]
        order = db_proxy.get_repair_order(uuid)

        await self.answer(query, order.update(status, self.get_master(query)))

    def _make_order_change_msg(self, order):
        return "\n".join(
            [
                order.get_title(),
                order.get_description(),
                order.get_status(),
                "\n",
                order.get_tracking_link(),
                order.get_created_time(),
            ]
        )

    async def handle_item(self, update, context):
        query, route = await self.parse_update(update)
        uuid = route[self.UUID]
        order = db_proxy.get_repair_order(uuid)

        self.init_builder(route)
        self.builder.add_status_switch(uuid, order.status)
        self.builder.add_back_btn()

        await self.answer(query, self._make_order_change_msg(order), self.builder.product)


    async def handle_page(self, update, context):
        query, route = await self.parse_update(update)

        page = db_proxy.get_order_page(self._get_page(route), self.get_master(query).id)

        self.init_builder(route)
        for i in page.items:
            self.builder.add_button(
                text=f"{i.model} {truncate(i.problem, self.DESC_LEN)}",
                callback=f"/order/{i.uniq_link}/",
            )
        self.builder.add_pager()

        await self.answer(query, "Меню", self.builder.product)


class SpareHandler(AbstractHandler):

    CATEG_ID = 1
    PAGE_NUM = 1

    def __init__(self, bridge):
        self.bridge = bridge
        self.builder = bridge.builder
        self.updated_spares_id = None

        bridge.app.add_handler(
            CallbackQueryHandler(self.handle_page, pattern=Routes.spares)
        )
        bridge.app.add_handler(
            CallbackQueryHandler(self.handle_category, pattern=Routes.spares_subtype)
        )
        bridge.app.add_handler(CallbackQueryHandler(self.handle_item, pattern=Routes.spare))
        # bridge.app.add_handler(
        #     ConversationHandler(
        #         entry_points=[
        #             CallbackQueryHandler(
        #                 self.get_ready_for_update, pattern=Routes.spare_upload
        #             )
        #         ],
        #         states={
        #             self.WAIT_FOR_UPDATE: [
        #                 MessageHandler(filters.ATTACHMENT, self.wait_for_update)
        #             ]
        #         },
        #         fallbacks=[CallbackQueryHandler(self.reset_state, pattern="^reset$")],
        #     )
        # )
        bridge.app.add_handler(
            CallbackQueryHandler(self.download, pattern=Routes.spare_download)
        )

    async def reset_state(self, update, context):
        self.updated_spares_id = None
        return ConversationHandler.END

    async def get_ready_for_update(self, update, context):
        data = await self.catch_update(update)

        self.updated_spares_id = self.get_route_data(data)
        return self.WAIT_FOR_UPDATE

    async def wait_for_update(self, update, context):
        try:
            document_update = SpareUpdate(
                await update.message.document.get_file(),
                update.message.document.file_name,
            )
            await document_update.download()
            document_update.parse()
            document_update.delete()
            self.updated_spares_id = None

            return ConversationHandler.END

        except Exception as e:

            self.builder.add_button("⬅️", "reset")
            await self.bot.send_message(
                f"Произошла ошибка\n```{e.__repr__()}```.\n Попробуйте снова",
                markup=self.builder.product,
            )
            return self.WAIT_FOR_UPDATE

    async def handle_item(self, update, context):
        query, route = await self.parse_update(update)
        categ_id = route[self.CATEG_ID]
        categ = db_proxy.get_category_by_id(categ_id)

        self.init_builder(route)
        self.builder.add_file_toggle(categ_id)
        self.builder.add_back_btn()

        await self.answer(query, str(categ), self.builder.product)

    async def handle_category(self, update, context):
        query, route = await self.parse_update(update)

        self.init_builder(route)
        page = db_proxy.get_categories_page(self.builder.max_per_page, page)
        for i in page.items:
            self.builder.add_button(text=f"{i.name}", callback=f"/spares/{i.id}/")
        self.builder.add_pager()
        
        await self.answer(query, "Меню", self.builder.product)

    async def handle_page(self, update, context):
        query, route = await self.parse_update(update)
        page = db_proxy.get_categories_page(self._get_page(route))

        self.init_builder(route)
        for i in page.items:
            self.builder.add_button(
                text=f"{i.name}", callback=f"/spares/{i.id}/"
            )
        self.builder.add_pager()

        await self.answer(query, "Меню", self.builder.product)

    async def download(self, update, context):
        query, route = await self.parse_update(update)
        category_name, header, lines = db_proxy.export_category_to_csv(route[self.CATEG_ID])
        filename = f"instance/{category_name}.csv"

        with open(filename, "w") as f:
            writer = csv.writer(f)
            writer.writerow(header)
            for line in lines:
                writer.writerow(line)

        await self.bridge.send_document(filename)


class TelegramBridge(metaclass=Singleton):

    def __init__(self, token, chat, flask, max_page_size=5):
        self.app = Application.builder().token(token).build()
        self.chat = chat
        self.builder = InlineKeyboardUIBuilder(max_page_size)

        self.app.add_handler(
            TypeHandler(type=FlaskUpdate, callback=self.send_new_order)
        )

    def register(self, *handlers):
        for i in handlers:
            i(self) if is_class(i) else None

    async def send_message(self, message, **kwargs):
        await self.app.bot.send_message(
            chat_id=self.chat,
            text=message,
            parse_mode=telegram.constants.ParseMode.MARKDOWN_V2,
            reply_markup=kwargs.get("markup"),
        )

    async def add_update(self, update):
        await self.app.update_queue.put(FlaskUpdate(user_id=self.chat, payload=update))

    async def send_new_order(self, update: FlaskUpdate, context: CustomContext):
        uniq_link = update.payload
        order = db_proxy.get_order(uniq_link)
        self.builder.accept_order(uniq_link)
        await self.send_message(str(order), markup=self.builder.product)

    async def send_document(self, path):
        await self.app.bot.send_document(chat_id=self.chat, document=open(path, "rb"))

    async def edit_kb(self, query, kb):
        await query.edit_message_reply_markup(reply_markup=kb)

    async def edit_text(self, query, msg):
        await query.edit_message_text(
            text=msg,
            parse_mode=telegram.constants.ParseMode.MARKDOWN_V2,
        )


def start_bot(app):
    bot = TelegramBridge(TG_TOKEN, WORKING_CHAT, app)
    bot.register(SpareHandler, OrderHandler, MenuHandler, AdminHandler)

    return bot


@click.command("start-bot")
def start_bot_command():
    bot = TelegramBridge(TG_TOKEN, WORKING_CHAT)
    bot.register(SpareHandler, OrderHandler, MenuHandler, AdminHandler)

    bot.poll()
