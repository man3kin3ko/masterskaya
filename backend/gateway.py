import uuid
import logging
from fastapi import FastAPI

from starlette.middleware.cors import CORSMiddleware
from app.db_models import db, RepairOrder
from app.schemas import OrderFormRequestSchema

from app.telegram_bridge import bot

fast_api = FastAPI()
fast_api.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["POST", "GET", "PATCH"],
    allow_headers=["*"],
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


def save_data_db(order_form, order_uuid):
    new_order = RepairOrder(
        uniq_link=order_uuid,
        contact=order_form.contact,
        model=order_form.model,
        problem=order_form.problem,
        social_media_type=order_form.soc_type
    )

    db.session.add(new_order)
    db.session.commit()


@fast_api.post("/form")
async def read_item(order_form: OrderFormRequestSchema):
    try:
        new_order_uuid = str(uuid.uuid4())
        # save_data_db(order_form, new_order_uuid)

        # await bot.send_message("-1002225814460", new_order_message)
        await bot.send_new_order(order_form, new_order_uuid)

        return {}, 200
    except Exception as e:
        return {e.__repr__()}, 500