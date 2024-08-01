import uuid
from pydantic import BaseModel

from .db_models import SocialMediaType


class OrderFormRequestSchema(BaseModel):
    contact: str
    model: str
    problem: str
    soc_type: SocialMediaType

class OrderUUID(BaseModel):
    uuid: uuid.UUID