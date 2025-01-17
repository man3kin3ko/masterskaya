import uuid
from pydantic import BaseModel

class OrderFormRequestSchema(BaseModel):
    contact: str
    model: str
    problem: str
    soc_type: str

class OrderUUIDSchema(BaseModel):
    uuid: uuid.UUID