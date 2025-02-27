import asyncio
import uvicorn
import logging
from flask import request
from asgiref.wsgi import WsgiToAsgi

from app.frontend import app
from app.db import RepairOrder, DBProxy
from app.tg import start_bot

#https://docs.python-telegram-bot.org/en/stable/examples.customwebhookbot.html

logging.basicConfig(
    format="[MAIN] %(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

async def main() -> None:
    bot = start_bot(app)

    @app.route("/form", methods=["POST"])
    async def read_item():
        try:
            db_proxy = DBProxy()
            new_repair_order = RepairOrder.from_request(request.json)
            db_proxy.add_to_transaction(new_repair_order.create)
            db_proxy.execute_in_context()

            await bot.add_update(new_repair_order)
            return '', 200

        except Exception as e:
            logging.warning(e.__repr__())
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