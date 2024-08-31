import abc
import os
import sqlalchemy
import logging
import csv
import uuid
from datetime import datetime, timezone, timedelta
from telegram.helpers import escape_markdown
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.ext.hybrid import hybrid_property
from functools import wraps
from sqlalchemy import (
    Integer, 
    String,
    ForeignKey, 
    select, 
    insert, 
    update,
    )
from sqlalchemy.orm import (
    DeclarativeBase, 
    Mapped, 
    mapped_column, 
    relationship
    )

from .enums import (
    OrderFormRequestSchema, 
    OrderUUIDSchema, 
    Status, 
    SpareType, 
    SocialMediaType, 
    SpareAviability,
    BaseEnum
    )
from ..utils import Singleton

UTC_DELTA = 3
TIME_FORMAT = "%H:%M %d.%m.%Y"

# https://docs.sqlalchemy.org/en/14/_modules/examples/asyncio/async_orm.html

class Base(DeclarativeBase):
    pass


def with_app_context(action_type):
    def decorator(f):
        @wraps(f)
        def wrapper(self, *args):
            with self.app.app_context():
                if action_type == 'single':
                    return self.db.session.execute(f(self, *args)).first()[0]
                elif action_type == 'many':
                    return self.db.session.execute(f(self, *args)).all()
                else:
                    return f(self, *args)

        return wrapper
    return decorator

class DBProxy(metaclass=Singleton):
    def __init__(self, max_per_page=5):
        self.db = SQLAlchemy(model_class=Base)
        self.max_per_page = int(max_per_page)

    @staticmethod
    def validate_uuid(uuid):
        return OrderUUIDSchema(uuid=uuid).uuid

    def assign_app(self, app):
        self.app = app

    @with_app_context(action_type=None)
    def add(self, orm_object):
        self.db.session.add(orm_object)
        self.db.session.commit()

    @with_app_context(action_type=None)
    def update(self, cls, bulk:list):
        self.db.session.execute(
                    update(cls), bulk
                )
        self.db.session.commit()

    @with_app_context(action_type=None)
    def commit(self):
        self.db.session.commit()

    @with_app_context(action_type="single")
    def get_spare_by_category_and_brand(spare, brand, category):
        q = select(Spare).join(Brand).join(SpareCategory)
        q = q.where(Spare.brand_id == brand.id).where(Spare.categ_id == category.id)
        q = q.where(Spare.name == spare.name)
        return q
    
    @with_app_context(action_type=None)
    def refresh(self, orm_object):
        self.db.session.refresh(orm_object)

    @with_app_context(action_type='single')
    def get_repair_order(self, uuid, master_id=None):
        return select(RepairOrder).where(RepairOrder.uniq_link == str(self.validate_uuid(uuid)))

    @with_app_context(action_type=None)
    def export_category_to_csv(self, categ_id):
        header = ['name', 'quantity', 'price', 'brand']

        category_name = self.db.session.execute(
            select(SpareCategory.prog_name).where(SpareCategory.id == int(categ_id))
        ).first()[0]
            
        records = self.db.session.execute(
            select(Spare, Brand.name, Brand.country)
            .join(Spare.categ)
            .join(Spare.brand)
            .where(SpareCategory.id == int(categ_id))
            .order_by(Brand.id)
            ).all()

        lines = [i[0].serialize() + [i[1], i[2]] for i in records]

        return category_name, header, lines

    @with_app_context(action_type='single')
    def get_spare(self, spare_id):
        return select(Spare).where(Spare.id == int(spare_id))

    @with_app_context(action_type=None)
    def get_spares_by_category_and_type(self, spare_type, spare_category):
        spares = self.db.session.execute(
            select(Spare, Brand.name)
            .join(Spare.brand)
            .join(Spare.categ)
            .where(SpareCategory.type == spare_type)
            .where(SpareCategory.prog_name == spare_category)
            .order_by(Brand.id)
            ).all()

        brands = self.db.session.execute(
            select(Brand.name)
                .join(Spare.brand)
                .join(Spare.categ)
                .where(SpareCategory.type == spare_type)
                .where(SpareCategory.prog_name == spare_category)
                .order_by(Brand.id)
                .distinct()
            ).all()

        return spares, brands

    @with_app_context(action_type='many')
    def get_spares_by_category(self, spare_category_id):
        return select(Spare).join(Spare.brand).join(Spare.categ).where(SpareCategory.id == spare_category_id).order_by(Brand.id)
    
    @with_app_context(action_type='single')
    def get_category_by_id(self, categ_id):
        return select(SpareCategory.name).where(SpareCategory.id == int(categ_id))

    @with_app_context(action_type='single')
    def get_category_by_name(self, prog_name):
        return select(SpareCategory).where(SpareCategory.prog_name == prog_name)

    @with_app_context(action_type='single')
    def is_repair_order_exist(self, uuid):
        return select(RepairOrder.uniq_link).where(RepairOrder.uniq_link == str(self.validate_uuid(uuid)))

    @with_app_context(action_type='many')
    def get_categories(self):
        return select(SpareCategory)

    @with_app_context(action_type=None)
    def get_categories_page(self, page):
        return self.db.session.query(
                SpareCategory.id, SpareCategory.name
                ).paginate(page=int(page), max_per_page=self.max_per_page)

    @with_app_context(action_type=None)
    def get_order_page(self, page, master_id):
        return self.db.session.query(
                RepairOrder.uniq_link, 
                RepairOrder.problem, 
                RepairOrder.model
                ).where(
                    RepairOrder.master_id == master_id
                    ).paginate(page=int(page), max_per_page=self.max_per_page)

    @with_app_context(action_type='single')
    def get_order(self, uuid):
        return select(RepairOrder).where(RepairOrder.uniq_link == uuid)

    @with_app_context(action_type='single')
    def get_brand_by_name(self, name):
        return select(Brand).where(Brand.name == name)

db_proxy = DBProxy()

class CSVParseable():
    __metaclass__ = abc.ABCMeta
    @abc.abstractmethod
    def from_csv(attrs: dict):
        pass

    @classmethod
    def serialize(cls, record):
        return map(
                    lambda x: x.name if issubclass(x.__class__, BaseEnum) else x, 
                    [ getattr(record[0], i.name, None) for i in cls.__mapper__.columns ]
                )

    @classmethod
    def get_header(cls):
        # cls.__mapper__.all_orm_descriptors.keys() for unions?
        return [i.key for i in cls.__mapper__.columns]

    @staticmethod
    def deserialize(obj, attr, attr_cls):
        if obj.get(attr):
            if issubclass(attr_cls, BaseEnum):
                obj[attr] = attr_cls[obj[attr]]
            if attr_cls == int:
                obj[attr] = int(obj[attr])
            if issubclass(attr_cls, datetime):
                # ! exel зачем-то ломает iso
                obj[attr] = datetime.strptime(obj[attr], '%Y-%m-%d %H:%M:%S.%f')


class SpareUpdate(CSVParseable):
    def __init__(self, file, filename):
        self.file = file
        self.path = f"/tmp/{file.file_id}"
        self.category = db_proxy.get_category_by_name(filename.rstrip('.csv'))
    
    async def download(self):
        await self.file.download_to_drive(custom_path=self.path)

    def delete(self):
        os.remove(self.path)

    def parse(self):
        with open(self.path) as f:
            reader = csv.reader(f)
            header = next(reader)[:-1]
            updates = []
            for row in reader:
                brand = db_proxy.get_brand_by_name(row.pop())
                spare = Spare(**Spare.from_csv(dict(zip(header, row))))
                try:
                    spare = db_proxy.get_spare_by_category_and_brand(
                        spare, brand, self.category
                        )
                    updates.append(spare)
                except TypeError:
                    spare.categ_id = self.category.id
                    spare.brand_id = brand.id
                    db_proxy.add(spare)

            db_proxy.update(updates)


class RepairOrder(db_proxy.db.Model, CSVParseable):
    __tablename__ = "repairs"

    id: Mapped[int] = mapped_column(primary_key=True)
    uniq_link: Mapped[str] = mapped_column(String(36), nullable=False, unique=True, index=True)
    contact: Mapped[str] = mapped_column()
    social_media_type: Mapped[SocialMediaType] = mapped_column()
    status: Mapped[Status] = mapped_column(default=Status.ORDERED)
    problem: Mapped[str] = mapped_column()
    model = mapped_column(String(50), nullable=False)
    created_time: Mapped[datetime] = mapped_column(
        sqlalchemy.DateTime,
        default=datetime.now(timezone.utc),
    )
    last_modified_time: Mapped[datetime] = mapped_column(
        sqlalchemy.DateTime,
        default=datetime.now(timezone.utc),
        onupdate=datetime.now(timezone.utc),
    )
    master_id: Mapped[int] = mapped_column(nullable=True)

    @classmethod
    def from_csv(cls, attrs):
        cls.deserialize(attrs, "id", int)
        cls.deserialize(attrs, "status", Status)
        cls.deserialize(attrs, "created_time", datetime)
        cls.deserialize(attrs, "last_modified_time", datetime)
        cls.deserialize(attrs, "social_media_type", SocialMediaType)
        return attrs

    def save(self):
        db_proxy.add(self)

    def get_title(self):
        return f"Заказ от \[{escape_markdown(self.social_media_type.value, version=2)}\] {escape_markdown(self.contact, version=2)}\n\nМодель {escape_markdown(self.model, version=2)}"

    def get_uuid(self):
        return f"Номер заказа: `{self.uniq_link}`"

    def get_tracking_link(self):
        return f"Трекинговая ссылка: `https://masterskaya35.ru/tracking/{self.uniq_link}`"

    def get_status(self):
        return f"Статус: `{self.status}`"

    def get_modified_time(self):
        return f"Обновлен: {escape_markdown(self._last_modified_time, version=2)}"

    def get_created_time(self):
        return f"Создан: {escape_markdown(self._created_time, version=2)}"

    def get_description(self):
        return f"```Описание\n{self.problem}```\n"

    @hybrid_property
    def _social_media_type(self): 
        return SocialMediaType[self.social_media_type]
    
    @hybrid_property
    def _last_modified_time(self):
        return (self.last_modified_time + timedelta(hours=UTC_DELTA)).strftime(TIME_FORMAT)

    @hybrid_property
    def _created_time(self):
        return (self.created_time + timedelta(hours=UTC_DELTA)).strftime(TIME_FORMAT)

    def __str__(self):
        return "\n".join([
            self.get_title(),
            f"\n\n```{self.problem}```\n\n",
            self.get_created_time(),
            self.get_uuid()
        ])

    @staticmethod
    def from_request(json_data):
        schema = OrderFormRequestSchema(**json_data)
        order = RepairOrder(
            uniq_link = str(uuid.uuid4()),
            contact = schema.contact,
            social_media_type = schema.soc_type.name,
            problem = schema.problem,
            model = schema.model
        )
        return order
    
    def update(self, status, master):
        # for some reason were out of session so we cannot update db state by changing attributes
        # flask-sqlalchemy-session is also useless here therefore we use asyncio flask which has broken 
        # this library

        with db_proxy.app.app_context():
            db_proxy.db.session.execute(
                update(RepairOrder)
                .where(RepairOrder.uniq_link == self.uniq_link)
                .values(status=Status(status).name, master_id=master.id)
            )
            db_proxy.db.session.commit()
        updated = db_proxy.get_order(self.uniq_link)

        return "\n".join([
            f"Заказ `{updated.uniq_link}` изменен {master.first_name} {master.last_name if master.last_name else ''}\n",
            updated.get_status(),
            updated.get_modified_time()
            ])


class Brand(db_proxy.db.Model, CSVParseable):
    __tablename__ = "brand"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(256), nullable=False, primary_key=True)
    country: Mapped[str] = mapped_column(String(2), nullable=False)

    @classmethod
    def from_csv(cls, attrs):
        cls.deserialize(attrs, "id", int)
        return attrs


class Spare(db_proxy.db.Model, CSVParseable):
    __tablename__ = "spares"

    id: Mapped[int] = mapped_column(primary_key=True)
    brand_id: Mapped[int] = mapped_column(Integer, ForeignKey("brand.id"), nullable=False)
    brand = relationship("Brand")
    categ_id: Mapped[int] = mapped_column(Integer, ForeignKey("spare_category.id"), nullable=False)
    categ: Mapped[str] = relationship("SpareCategory")
    name: Mapped[str] = mapped_column(String(256), nullable=False, index=True)
    availability: Mapped[SpareAviability] = mapped_column(default=SpareAviability.UNKNOWN)
    price: Mapped[int] = mapped_column(Integer)
    quantity: Mapped[int] = mapped_column(Integer, default=0)
    
    @classmethod
    def from_csv(cls, attrs):
        cls.deserialize(attrs, "id", int)
        cls.deserialize(attrs, "price", int)
        cls.deserialize(attrs, "quantity", int)
        cls.deserialize(attrs, "categ_id", int)
        cls.deserialize(attrs, "aviability", SpareAviability)
        return attrs

    def serialize(self, header):
        return list(map(
                lambda x: x.name if issubclass(x.__class__, BaseEnum) else x, 
                [ getattr(self, i.name, None) for i in self.__mapper__.columns if i in header]
            ))


class SpareCategory(db_proxy.db.Model, CSVParseable):
    __tablename__ = "spare_category"

    id: Mapped[int] = mapped_column(primary_key=True)
    type: Mapped[SpareType] = mapped_column()
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    description: Mapped[str] = mapped_column(String(256))
    image_name: Mapped[str] = mapped_column(String(30))
    prog_name: Mapped[str] = mapped_column(String(30))

    def __str__(self):
        return self.name

    @classmethod
    def from_csv(cls, attrs):
        cls.deserialize(attrs, "id", int)
        cls.deserialize(attrs, "type", SpareType)

    def is_empty(self):
        return len(db_proxy.get_spares_by_category(self.id)) > 0

    def get_store_link(self):
        return f"/store/spares/{self.type.value}/{self.prog_name}/"