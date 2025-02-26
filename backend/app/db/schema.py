import uuid
from pydantic import BaseModel
from typing import Literal

class OrderFormRequestSchema(BaseModel):
    contact: str
    model: str
    problem: str
    soc_type: Literal['vk', 'tg', 'phone', 'email']

class OrderUUIDSchema(BaseModel):
    uuid: uuid.UUID