import asyncio
import uvicorn
import logging
from app.flask_app import app
import app.db as db
from flask import request
from asgiref.wsgi import WsgiToAsgi
from app.tg import start_bot

#https://docs.python-telegram-bot.org/en/stable/examples.customwebhookbot.html

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.DEBUG
)
logger = logging.getLogger(__name__)

async def main() -> None:
    bot = start_bot(app)

    @app.route("/form", methods=["POST"])
    async def read_item():
        try:
            new_repair_order = db.RepairOrder.from_request(request.json)
            uniq_link = new_repair_order.uniq_link

            new_repair_order.save()

            await bot.add_update(uniq_link)
            return '', 200

        except Exception as e:
            logging.debug(e.__repr__())
            return '', 500

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
        await bot.app.updater.start_polling()
        await webserver.serve()
        await bot.app.updater.stop()
        await bot.app.stop()

if __name__ == '__main__':
    asyncio.run(main())