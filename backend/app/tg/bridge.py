import os
import abc
import csv
import httpx
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

from app.tg.ui import InlineKeyboardUIBuilder, Route
from app.utils import truncate, Singleton, async_to_sync, is_class
from app.db import DBProxy
import app.db as db

db_proxy = DBProxy()
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
    def get_master(query):
        return query.from_user

    def get_builder(self, route):
        if not isinstance(route, Route):
            route = Route.from_uri(route)
        return InlineKeyboardUIBuilder(self.bridge.max_per_page, route)

    async def parse_update(self, update):
        query = await self.catch_update(update)
        route = Route.from_uri(query.data)
        return query, route

    async def catch_update(self, update):
        query = update.callback_query
        await query.answer()

        return query

    async def answer(self, query, text, kb=None):
        await self.bridge.edit_text(query, text)
        if kb is not None:
            await self.bridge.edit_kb(query, kb)


class MenuHandler(AbstractHandler):
    def __init__(self, bridge):
        self.title = "Меню"
        self.bridge = bridge
        bridge.app.add_handler(CallbackQueryHandler(self.answer_menu, pattern=Route.registred["menu"]))
        bridge.app.add_handler(CommandHandler("menu", self.send_menu))
    
    def _make_menu(self):
        builder = self.get_builder("/menu/")
        builder.make_menu()
        return builder.product

    async def send_menu(self, update: Update, context: CustomContext):
        await self.bridge.send_message(message=self.title, markup=self._make_menu())

    async def answer_menu(self, update, context):
        query, route = await self.parse_update(update)
        await self.answer(query, self.title, self._make_menu())



class OrderHandler(AbstractHandler):
    def __init__(self, bridge):
        self.bridge = bridge
        bridge.app.add_handler(
            CallbackQueryHandler(self.handle_page, pattern=Route.registred["orders"])
        )
        bridge.app.add_handler(
            CallbackQueryHandler(self.handle_item, pattern=Route.registred["order"])
        )
        bridge.app.add_handler(
            CallbackQueryHandler(self.change_item, pattern=Route.registred["order_change"])
        )

    async def change_item(self, update, context):
        query, route = await self.parse_update(update)
        master = self.get_master(query)

        order = db.repair_order_by_uuid(db_proxy.create_session(), route.uuid)
        order.status = route.status
        order.master_id = master.id

        db_proxy.add_to_transaction(order.update)
        db_proxy.execute_in_context()

        await self.answer(query, order.update_msg(master))


    async def handle_item(self, update, context):
        query, route = await self.parse_update(update)
        order = db.repair_order_by_uuid(db_proxy.create_session(), route.uuid)

        builder = self.get_builder(route)
        builder.add_status_switch(route.uuid, order.status)
        builder.add_back_btn()

        await self.answer(query, order.full_info(), builder.product)


    async def handle_page(self, update, context):
        query, route = await self.parse_update(update)
        master = self.get_master(query)
        page_num = route.match
        page = db.repair_orders_page_by_master(db_proxy.create_session(), master.id, page_num)

        builder = self.get_builder(route)
        for i in page:
            builder.add_button(
                text=f"№{i.id} {truncate(i.problem, self.bridge.desc_len)}",
                callback=f"/order/item/{i.uuid}/",
            )
        builder.add_pager()

        await self.answer(query, "Меню", builder.product)


class SpareHandler(AbstractHandler):
    def __init__(self, bridge):
        self.bridge = bridge
        self.updated_spares_id = None
        bridge.app.add_handler(
            CallbackQueryHandler(self.handle_entry, pattern=Route.registred["spares"])
        )
        bridge.app.add_handler(
            CallbackQueryHandler(self.handle_page, pattern=Route.registred["spares_page"])
        )
        bridge.app.add_handler(CallbackQueryHandler(self.handle_item, pattern=Route.registred["spare"]))
        # bridge.app.add_handler(
        #     ConversationHandler(
        #         entry_points=[
        #             CallbackQueryHandler(
        #                 self.get_ready_for_update, pattern=Route.registred["spare_upload"]
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
            CallbackQueryHandler(self.download, pattern=Route.registred["spare_download"])
        )

    async def reset_state(self, update, context):
        self.updated_spares_id = None
        return ConversationHandler.END

    async def get_ready_for_update(self, update, context):
        data = await self.catch_update(update)

        self.updated_spares_id = self.get_route_data(data)
        return self.WAIT_FOR_UPDATE

    async def wait_for_update(self, update, context):
        query, route = await self.parse_update(update)
        try:
            # document_update = SpareUpdate(
            #     await update.message.document.get_file(),
            #     update.message.document.file_name,
            # )
            # await document_update.download()
            # document_update.parse()
            # document_update.delete()
            # self.updated_spares_id = None

            return ConversationHandler.END

        except Exception as e:
            builder = self.get_builder(route)
            builder.add_button("Закрыть", "reset")
            await self.bot.send_message(
                f"Произошла ошибка\n```{e.__repr__()}```.\n Попробуйте снова",
                markup=builder.product,
            )
            return self.WAIT_FOR_UPDATE

    async def handle_entry(self, update, context):
        query, route = await self.parse_update(update)
        builder = self.get_builder(route)
        builder.make_spares()
        await self.answer(query, "Меню", builder.product)

    async def handle_item(self, update, context):
        query, route = await self.parse_update(update)
        categ = db_proxy.get_category_by_id(route.id)

        builder = self.get_builder(route)
        builder.add_file_toggle(route.id)
        builder.add_back_btn()

        await self.answer(query, str(categ), builder.product)

    async def handle_page(self, update, context):
        query, route = await self.parse_update(update)
        page = db_proxy.get_categories_page(route.id)
        builder = self.get_builder(route)
        for i in page.items:
            builder.add_button(
                text=f"{i.name}", callback=f"/spare/{route.subtype}/item/{i.id}/"
            )
        builder.add_pager()

        await self.answer(query, "Меню", builder.product)

    async def download(self, update, context):
        query, route = await self.parse_update(update)
        category_name, header, lines = db_proxy.export_category_to_csv(route.match)
        filename = f"instance/{category_name}.csv"

        with open(filename, "w") as f:
            writer = csv.writer(f)
            writer.writerow(header)
            for line in lines:
                writer.writerow(line)

        await self.bridge.send_document(filename)


class TelegramBridge(metaclass=Singleton):
    def __init__(self, token, chat, flask, max_per_page=5, desc_len=10):
        self.app = Application.builder().token(token).build()
        self.chat = chat
        self.max_per_page = max_per_page
        self.desc_len = desc_len
        self.app.add_handler(
            TypeHandler(type=FlaskUpdate, callback=self.send_new_order)
        )
        #self.app.add_error_handler(self.error_handler)

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

    async def error_handler(self, update, context: ContextTypes.DEFAULT_TYPE):
        await self.send_message(f"Non\-fatal error has occured:\n```{context.error}```")

    async def send_new_order(self, update: FlaskUpdate, context: CustomContext):
        order = update.payload
        builder = InlineKeyboardUIBuilder.from_flask_update(self.max_per_page, order.uuid)

        await self.send_message(str(order), markup=builder.product)

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
    bot.register(SpareHandler, OrderHandler, MenuHandler)

    return bot
