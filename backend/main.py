import asyncio
import uvicorn
import logging
import uuid
from app.run import app
import app.db_models as db
from flask import request
from app.schemas import OrderFormRequestSchema
from asgiref.wsgi import WsgiToAsgi
from app.telegram_bridge import TG_TOKEN, WORKING_CHAT, TelegramBridge

#https://docs.python-telegram-bot.org/en/stable/examples.customwebhookbot.html

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.DEBUG
)
logger = logging.getLogger(__name__)

async def main() -> None:
    bot = TelegramBridge(TG_TOKEN, WORKING_CHAT)

    @app.route("/form", methods=["POST"])
    async def read_item():
        try:
            new_repair_order = OrderFormRequestSchema(**request.json)
            new_order_uuid = str(uuid.uuid4())
            db.save_repair_order(new_repair_order, new_order_uuid)

            await bot.send_new_order(new_repair_order, new_order_uuid)

            return '', 200
        except Exception as e:
            return f'{e.__repr__()}', 500 # change later :3

    webserver = uvicorn.Server(
        config=uvicorn.Config(
        app=WsgiToAsgi(app),
        port=5000,
        use_colors=False,
        host="0.0.0.0",
        )
    )

    async with bot.app:
        await bot.app.start()
        await webserver.serve()
        await bot.app.stop()

if __name__ == '__main__':
    asyncio.run(main())