import uuid
import logging
from fastapi import FastAPI
from pydantic import BaseModel
from starlette.middleware.cors import CORSMiddleware
from app.db_models import db, RepairOrder, SocialMediaType
from app.telegram_bridge import send_message_via_bot, TG_TOKEN
from app.dungeon_masters import MastersChatId
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


class OrderFormRequestSchema(BaseModel):
    contact: str
    model: str
    problem: str
    soc_type: SocialMediaType


@app.get("/catalog")
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


@app.post("/form")
def read_item(order_form: OrderFormRequestSchema):
    try:
        save_data_db(order_form, str(uuid.uuid4()))
        send_message_via_bot(TG_TOKEN, MastersChatId.Onjey, "Привет")
        return {}, 200
    except Exception as e:
        return {e.__repr__()}, 500


@app.post("/super_sec_root_with_very_long_sec_name")
def f():
    pass