import os
import logging
from flask import Flask, request
from .db_models import db, RepairOrder, SocialMediaType
from .telegram_bridge import TelegramBridge

app = Flask(__name__)
bot = TelegramBridge(os.environ["TOKEN"])
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


@app.route("/submit_form", methods=["POST"])
def repair_submit_form():
    try:
        new_order = RepairOrder(
            contact=request.form["contact"],
            model=request.form["model"],
            problem=request.form["problem"],
            social_media_type=SocialMediaType.__dict__[request.form["soc_type"]]
        )
        db.session.add(new_order)
        db.session.commit()

        bot.send(str(new_order))
        return {}, 200
    except Exception as e:
        logger.error(e.__str__())
        return {}, 500
