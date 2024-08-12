import enum
import datetime
import sqlalchemy
import csv
import uuid
from ..utils import Singleton
from flask import g
from pydantic import BaseModel
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import (
    Integer, 
    ForeignKey, 
    select, 
    insert, 
    update
    )
from sqlalchemy.orm import (
    DeclarativeBase, 
    Mapped, 
    mapped_column, 
    relationship
    )

class Base(DeclarativeBase):
    pass

class DBProxy(metaclass=Singleton):
    def __init__(self, max_per_page=5):
        self.db = SQLAlchemy(model_class=Base)
        self.max_per_page = int(max_per_page)

    @staticmethod
    def validate_uuid(uuid):
        return OrderUUID(uuid).uuid

    def assign_app(self, app):
        self.app = app
    
    def get_repair_order(self, uuid):
        uuid = self.validate_uuid(uuid)
        with self.app.app_context():
            return RepairOrder.query.where(RepairOrder.uniq_link == str(uuid))
    
    def get_repair_orders(self, master_id, page):
        with self.app.app_context():
            return RepairOrder.query.where(RepairOrder.master_id == master_id).paginate(page=int(page), max_per_page=self.max_per_page)

    def export_category_to_csv(self, categ_id):
        with self.app.app_context():
            records = self.db.session.execute(
                select(Spare)
                .join(Spare.categ)
                .join(Spare.brand)
                .where(SpareCategory.id == int(categ_id))
                .order_by(Brand.id)
                ).all()
            with open('temp.csv', 'w') as f:
                outcsv = csv.writer(f)
                for c in records:
                    outcsv.writerow([getattr(c[0], i.name, None) for i in Spare.__mapper__.columns]) 

    def get_spares_by_category_and_type(self, spare_type, spare_category):
        with self.app.app_context():
            return self.db.session.execute(
                select(Spare)
                .join(Spare.brand)
                .join(Spare.categ)
                .where(SpareCategory.type == spare_type)
                .where(SpareCategory.prog_name == spare_category)
                .order_by(Brand.id)
                ).all()
    
    def get_spares_by_category(self, spare_category):
        with self.app.app_context():
            return self.db.session.execute(
                select(Spare)
                .join(Spare.brand)
                .join(Spare.categ)
                .where(SpareCategory.id == spare_category_id)
                .order_by(Brand.id)
                ).all()

    def get_brands_by_category_and_type(self, spare_type, spare_category):
        with self.app.app_context():
            return self.db.session.execute(
                select(Brand.name)
                .join(Spare.brand)
                .join(Spare.categ)
                .where(SpareCategory.type == spare_type)
                .where(SpareCategory.prog_name == spare_category)
                .order_by(Brand.id)
                .distinct()
                ).all()
    
    def get_category_by_id(self, categ_id):
        with self.app.app_context():
            return self.db.session.execute(
                select(SpareCategory.name).where(SpareCategory.id == int(categ_id))
            ).first()

    def get_category_by_name(self, prog_name):
        with self.app.app_context():
            return self.db.session.execute(
                select(SpareCategory).where(SpareCategory.prog_name == prog_name)
            ).first()[0]

    def is_repair_order_exist(self, uuid):
        uuid = self.validate_uuid(uuid)
        with self.app.app_context():
            return self.db.session.execute(
                select(RepairOrder.uniq_link).where(RepairOrder.uniq_link == str(uuid))
            ).first()

    def get_categories(self):
        with self.app.app_context():
            return self.db.session.execute(
                select(SpareCategory)
                ).all()

    def get_categories_page(self, max_per_page, page):
        with self.app.app_context():
            return self.db.session.query(
                SpareCategory.id, SpareCategory.name
                ).paginate(page=int(page), max_per_page=self.max_page_size)

def get_order_page(max_per_page, page, master_id):
    with self.app.app_context():
        return self.db.session.query(
            RepairOrder.uniq_link, 
            RepairOrder.problem, 
            RepairOrder.model
            ).where(
                RepairOrder.master_id == master_id
                ).paginate(page=int(page), max_per_page=self.max_page_size)

db_proxy = DBProxy()

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
            'ordered':'Зарегестрирован',
            'accepted':'Принят в очередь работ',
            'in_progress':'В работе',
            'ready':'Готов',
            'closed':'Завершен',
            'problem':'Требуется ваше внимание'
        }
        return rus[item.value]

class SocialMediaType(enum.Enum):
    PHONE = "phone"
    EMAIL = "email"
    TG = "tg"
    VK = "vk"

class SpareType(enum.Enum):
    MECHA = "mecha"
    ELECTRIC = "electrical"
    def __str__(item):
        rus = {
            'mecha':'Механика',
            'electrical':'Электроника'
        }
        return rus[item.value]

class SpareAviability(enum.Enum):
    UNKNOWN = "Уточняйте"
    AVAILABLE = "В наличии"
    UNAVAILABLE = "Отсутствует"

class OrderFormRequestSchema(BaseModel):
    contact: str
    model: str
    problem: str
    soc_type: SocialMediaType

class OrderUUID(BaseModel):
    uuid: uuid.UUID

class RepairOrder(db_proxy.db.Model):
    __tablename__ = "repairs"

    id: Mapped[int] = mapped_column(primary_key=True)
    uniq_link = db_proxy.db.Column(db_proxy.db.String(36), nullable=False, unique=True)
    contact: Mapped[str] = mapped_column()
    social_media_type: Mapped[SocialMediaType] = mapped_column()
    status: Mapped[Status] = mapped_column(default=Status.ORDERED)
    problem: Mapped[str] = mapped_column()
    model = db_proxy.db.Column(db_proxy.db.String(50), nullable=False)
    created_time = db_proxy.db.Column(
        sqlalchemy.DateTime,
        default=datetime.datetime.utcnow,
    )
    last_modified_time = db_proxy.db.Column(
        sqlalchemy.DateTime,
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.now,
    )
    master_id: Mapped[int] = mapped_column(nullable=True)

    def __repr__(self):
        return f"Заказ от \[{self.social_media_type.value}\] {self.contact}\n\nМодель {self.model}\n\n```{self.problem}```\n\nНомер заказа: `{self.uniq_link}`"

    @staticmethod
    def from_request(json_data):
        schema = OrderFormRequestSchema(**json_data)
        return RepairOrder(
            uniq_link = str(uuid.uuid4()),
            contact = schema.contact,
            social_media_type = schema.soc_type.name,
            problem = schema.problem,
            model = schema.model
        )
    
    def save(self):
        db_proxy.db.session.add(self)
        db_proxy.db.session.commit()
    
    def update(self, status):
        self.status = Status(status).name
        # db.session.execute(
        #     update(RepairOrder)
        #     .where(RepairOrder.uniq_link == uuid)
        #     .values(status=Status(status).name, master_id=master_id)
        # )
        # db.session.commit()


class Brand(db_proxy.db.Model):
    __tablename__ = "brand"
    id = mapped_column(Integer, primary_key=True)
    name = db_proxy.db.Column(db_proxy.db.String(256), nullable=False)
    country = db_proxy.db.Column(db_proxy.db.String(2))


class Spare(db_proxy.db.Model):
    __tablename__ = "spares"
    id = mapped_column(Integer, primary_key=True)
    brand_id = mapped_column(Integer, ForeignKey("brand.id"), nullable=False)
    brand = relationship("Brand")
    categ_id = mapped_column(Integer, ForeignKey("spare_category.id"), nullable=False)
    categ = relationship("SpareCategory")
    name = db_proxy.db.Column(db_proxy.db.String(256), nullable=False)
    availability: Mapped[SpareAviability] = mapped_column(default=SpareAviability.UNKNOWN)
    price = db_proxy.db.Column(Integer)
    quantity = db_proxy.db.Column(Integer, default=0)


class SpareCategory(db_proxy.db.Model):
    __tablename__ = "spare_category"
    id = mapped_column(Integer, primary_key=True)
    type: Mapped[SpareType] = mapped_column()
    name = db_proxy.db.Column(db_proxy.db.String(64), nullable=False)
    description = db_proxy.db.Column(db_proxy.db.String(256))
    image_name = db_proxy.db.Column(db_proxy.db.String(30))
    prog_name = db_proxy.db.Column(db_proxy.db.String(30))