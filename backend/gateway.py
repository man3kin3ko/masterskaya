import uuid
import logging
from fastapi import FastAPI

from starlette.middleware.cors import CORSMiddleware
from app.db_models import db, RepairOrder
from app.schemas import OrderFormRequestSchema

from app.telegram_bridge import send_message_via_bot, TG_TOKEN
from app.dungeon_masters import MastersChatId
from app.messages_builder import build_new_order_message

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


@fast_api.get("/catalog")
def read_root():
    return {
        "Камеры": ["Крутая камера пиздец"],
        "Запчасти": {
            "Электроника": ["Эл. запчасть 1", "Эл. запчасть 2", "Эл. запчасть 3"],
            "Механика": ["Мех. деталь 1", "Мех. деталь 2", "Мех. деталь 3"]
        }
    }


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

        cur_master = MastersChatId.Boris
        new_order_message: str = build_new_order_message(order_form, new_order_uuid, cur_master.name)

        await send_message_via_bot(TG_TOKEN, cur_master.value, new_order_message)

        return {}, 200
    except Exception as e:
        return {e.__repr__()}, 500


@fast_api.patch("/orders/{order_id}/status/{order_status}")
async def set_order_status(order_id: str, order_status: str):
    res = {"order_id": order_id, "order_status": order_status}
    print(res)
    return res, 200



