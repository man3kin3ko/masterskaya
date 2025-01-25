import enum
from uuid import uuid4
from telegram.helpers import escape_markdown # если эскейпить на уровне модуля тг, то не будет, собственно, разметки - ну или как-то через format нужно передавать хз что называется TODO
from typing import Optional, List
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.ext.hybrid import hybrid_property

from datetime import datetime, timezone, timedelta

from app.db.schema import OrderFormRequestSchema


### data structures ###

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
    ordered = "Зарегистрирован"
    accepted = "Принят в очередь работ"
    in_progress = "В работе"
    ready = "Готов"
    closed = "Закрыт"
    problem = "Требуется согласовать вмешательство"


class SpareAviability(BaseEnum):
    unknown = "Уточняйте"
    available = "В наличии"
    unavailable = "Отсутствует"


### sqlalchemy models ###


class Base(DeclarativeBase):
    def create(self, session):
        session.expire_on_commit = False
        session.add(self)

    def update(self, session):
        session.expire_on_commit = False
        session.merge(self)

    def refresh(self, session):
        session.refresh(self)

    def delete(self, session):
        session.delete(self)


class Brand(Base):
    __tablename__ = "brands"

    id = Column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(256), nullable=False, unique=True)
    country: Mapped[str] = mapped_column(String(2), nullable=False)

    # One-to-Many relationship with Spare (one brand can have many Spares)
    spares: Mapped[List["Spare"]] = relationship(back_populates="brand")


class SpareCategory(Base):
    __tablename__ = "spare_categories"

    id = Column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    subtype = Column(String)  # discriminator
    slug = Column(String, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(256))
    image_name: Mapped[str] = mapped_column(String(30), default="lamel.png")

    # One-to-Many relationship with Spare (one category can have many Spares)
    spares: Mapped[List["Spare"]] = relationship(back_populates="category")

    __mapper_args__ = {
        "with_polymorphic": "*", 
        "polymorphic_on": "subtype"
        }
    
    @staticmethod
    def from_discriminator(discriminator):
        return SpareCategory.__mapper__.polymorphic_map[discriminator].class_

    @property
    def store_link(self):
        return f"/store/spares/{self.subtype}/{self.slug}/"

    def is_empty(self, session):
        table = self.__class__
        categ = session.query(table).where(table.id == self.id).one()
        return not bool(session.query(Spare).where(Spare.category_id == categ.id).first())


class ElectricalSpare(SpareCategory):
    __mapper_args__ = {
        "polymorphic_identity": "electrical"
        }

    @property
    def icon(self):
        return "⚡"

    @property
    def human_name(self):
        return "Электроника"


class MechanicalSpare(SpareCategory):
    __mapper_args__ = {
        "polymorphic_identity": "mecha"
        }

    @property
    def icon(self):
        return "⚙️"

    @property
    def human_name(self):
        return "Механика"


class CommonSpare(SpareCategory):
    __mapper_args__ = {
        "polymorphic_identity": "common"
        }

    @property
    def icon(self):
        return "🪛"

    @property
    def human_name(self):
        return "Общее"


class Spare(Base):
    __tablename__ = "spares"

    id = Column(Integer, primary_key=True)
    brand_id = Column(Integer, ForeignKey("brands.id"))
    category_id = Column(Integer, ForeignKey("spare_categories.id"))

    # Relationships
    brand: Mapped[Brand] = relationship(back_populates="spares")
    category: Mapped[SpareCategory] = relationship(back_populates="spares")

    name: Mapped[str] = mapped_column(String(256), nullable=False, index=True)
    availability: Mapped[SpareAviability] = mapped_column(
        default=SpareAviability.unknown
    )
    price: Mapped[Optional[int]] = mapped_column(Integer)
    quantity: Mapped[int] = mapped_column(Integer, default=0)


class ResaleCamera(Base):
    __tablename__ = "camera_resale"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(64))
    description: Mapped[str] = mapped_column(String(256))
    price: Mapped[Optional[int]] = mapped_column(Integer)
    quantity: Mapped[int] = mapped_column(Integer, default=0)
    avito_link: Mapped[Optional[str]] = mapped_column(String(256))

    images: Mapped[List["Image"]] = relationship(back_populates="resale_camera")


class Image(Base):
    __tablename__ = "resale_images"

    id: Mapped[int] = mapped_column(primary_key=True)
    resale_id = Column(Integer, ForeignKey("camera_resale.id"))
    resale_camera: Mapped[ResaleCamera] = relationship(back_populates="images")
    image_name: Mapped[Optional[str]]
    external_url: Mapped[Optional[str]]


class Order(Base):
    __tablename__ = "orders"
    id: Mapped[int] = mapped_column(primary_key=True)

    subtype = Column(String)  # discriminator

    @property
    def utc(self):
        UTC_DELTA = 3
        return UTC_DELTA
        
    @property
    def time_format(self):
        return "%H:%M 🕑 %d.%m.%Y"
    
    created_time: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now(timezone.utc),
    )

    last_modified_time: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now(timezone.utc),
        onupdate=datetime.now(timezone.utc),
    )

    @hybrid_property
    def _last_modified_time(self):
        return (self.last_modified_time + timedelta(hours=self.utc)).strftime(self.time_format)

    @hybrid_property
    def _created_time(self):
        return (self.created_time + timedelta(hours=self.utc)).strftime(self.time_format)

    __mapper_args__ = {
        "with_polymorphic": "*", 
        "polymorphic_on": "subtype"
        }


class RepairOrder(Order):
    __mapper_args__ = {
        "polymorphic_identity": "repair"
        }

    uuid: Mapped[str] = mapped_column(String(36), nullable=False, unique=True, index=True, default=str(uuid4()))
    contact: Mapped[str] = mapped_column(nullable=False)
    social_media_type = mapped_column(String(16), nullable=False)
    status: Mapped[Status] = mapped_column(default=Status.ordered)
    problem = Column(String)
    model = Column(String)
    master_id: Mapped[int] = mapped_column(nullable=True)

    @staticmethod
    def from_request(json_data):
        schema = OrderFormRequestSchema(**json_data)
        order = RepairOrder(
            contact = schema.contact,
            social_media_type = str(schema.soc_type),
            problem = schema.problem,
            model = schema.model
        )
        return order

    @staticmethod
    def from_data(contact, soc_type, problem, model, uuid_=None):
        order = RepairOrder(
            contact = contact,
            problem = problem,
            model = model
        )
        return order

    ### tg view methods ###

    @property
    def title(self):
        return (
            f"Заказ №{self.id} от \[{self.social_media_type}\] " 
            f"{escape_markdown(self.contact, version=2)}\n\n"
            f"Модель {escape_markdown(self.model, version=2)}"
        )
    
    @property
    def tracking_link(self):
        return f"Трекинговая ссылка: `https://masterskaya35.ru/tracking/{self.uuid}`"

    @property
    def status_text(self):
        return f"Статус: `{self.status.value}`"

    @property
    def modified_time_text(self):
        return f"Обновлен: {escape_markdown(self._last_modified_time, version=2)}"

    @property
    def created_time_text(self):
        return f"Создан: {escape_markdown(self._created_time, version=2)}"

    @property
    def description(self):
        return f"```Описание\n{self.problem}```\n"

    def update_msg(self, master):
        return "\n".join([
            f"Заказ `{self.uuid}` изменен {master.first_name} {master.last_name if master.last_name else ''}",
            self.status_text,
            self.modified_time_text
            ])

    def full_info(self):
        return "\n".join([
                self.title,
                self.description,
                self.status_text,
                "\n",
                self.tracking_link,
                self.created_time_text,
            ])

    def __str__(self):
        return "\n".join([
            self.title,
            self.description,
            self.created_time_text,
            self.tracking_link
        ])

    ### --- ###
    

# class SparesOrder(Order):
#     pass

# class ResaleOrder(Order):
#     pass