import enum
import uuid
from pydantic import BaseModel

class MetaEnum(enum.EnumMeta):
    def __contains__(cls, item):
        try:
            cls(item)
        except ValueError:
            return False
        return True 

class BaseEnum(enum.Enum, metaclass=MetaEnum):
    pass

class Status(BaseEnum):
    ORDERED = "ordered"
    ACCEPTED = "accepted"
    IN_PROGRESS = "in_progress"
    READY = "ready"
    CLOSED = "closed"
    PROBLEMS = "problem"
    def __str__(item):
        rus = {
            'ordered':'Зарегистрирован',
            'accepted':'Принят в очередь работ',
            'in_progress':'В работе',
            'ready':'Готов',
            'closed':'Завершен',
            'problem':'Требуется ваше внимание'
        }
        return rus[item.value]

class SocialMediaType(BaseEnum):
    PHONE = "phone"
    EMAIL = "email"
    TG = "tg"
    VK = "vk"

class SpareType(BaseEnum):
    MECHA = "mecha"
    ELECTRIC = "electrical"
    def __str__(item):
        rus = {
            'mecha':'Механика',
            'electrical':'Электроника'
        }
        return rus[item.value]

class SpareAviability(BaseEnum):
    UNKNOWN = "Уточняйте"
    AVAILABLE = "В наличии"
    UNAVAILABLE = "Отсутствует"

class OrderFormRequestSchema(BaseModel):
    contact: str
    model: str
    problem: str
    soc_type: SocialMediaType

class OrderUUIDSchema(BaseModel):
    uuid: uuid.UUID