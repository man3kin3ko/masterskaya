import enum
import datetime
import sqlalchemy
from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Integer, ForeignKey, select, insert
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from flask import current_app, g


class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

def get_db():
    if 'db' not in g:
        g.db = db
    return g.db


def close_db(e=None):
    db = g.pop('db', None)

    if db is not None:
        db.close()

def get_spares(spare_type, spare_category):
    return db.session.execute(
        select(Spare)
        .join(Spare.brand)
        .join(Spare.categ)
        .where(SpareCategory.type == spare_type)
        .where(SpareCategory.prog_name == spare_category)
        .order_by(Brand.id)
        ).all()

def get_brands(spare_type, spare_category):
    return db.session.execute(
        select(Brand.name)
        .join(Spare.brand)
        .join(Spare.categ)
        .where(SpareCategory.type == spare_type)
        .where(SpareCategory.prog_name == spare_category)
        .order_by(Brand.id)
        .distinct()
        ).all()

def get_human_name(spare_category):
    return db.session.execute(
        select(SpareCategory.name).where(SpareCategory.prog_name == spare_category)
    ).first()[0]

def get_categs():
    return db.session.execute(
        select(SpareCategory)
    ).all()

def save_repair_order(order_form, order_uuid):
    new_order = RepairOrder(
        uniq_link=order_uuid,
        contact=order_form.contact,
        model=order_form.model,
        problem=order_form.problem,
        social_media_type=order_form.soc_type
    )

    db.session.add(new_order)
    db.session.commit()

def init_db():
    db.session.execute(
            insert(Brand),
            [
                {"name": "Kodak", "country": "US"},
                {"name": "Canon", "country": "JP"},
                {"name": "Fujifilm", "country": "JP"},
                {"name": "Nikon", "country": "JP"},
                {"name": "Sony", "country": "JP"},
                {"name": "Sigma", "country": "JP"},
                {"name": "Pentax", "country": "JP"},
                {"name": "Olympus", "country": "JP"},
                {"name": "Panasonic", "country": "JP"},
                {"name": "Samsung", "country": "KR"},
                {"name": "Arsenal", "country": "SU"},
                {"name": "KMZ", "country": "SU"},
                {"name": "Lomo", "country": "SU"},
                {"name": "Zeiss", "country": "DE"},
                {"name": "Exacta", "country": "DE"},
                {"name": "Rolleiflex", "country": "DE"},
                {"name": "Balda", "country": "DE"},
                {"name": "Welta", "country": "DE"},
                {"name": "Agfa", "country": "DE"},
            ],
        )
    db.session.execute(
            insert(SpareCategory),
            [
                {
                    "name": "Затворы",
                    "type": "MECHA",
                    "description": "хуйхуйхуйхуйхуй",
                    "image_name": "test_categ1.png",
                    "prog_name": "shutter",
                },
                {
                    "name": "Затворы",
                    "type": "ELECTRIC",
                    "description": "хуйхуйхуйхуйхуй",
                    "image_name": "test_categ2.png",
                    "prog_name": "shutter",
                },
                {
                    "name": "Матрицы",
                    "type": "ELECTRIC",
                    "description": "хуйхуйхуйхуйхуй",
                    "image_name": "3b71160fc60290752cb7.jpg",
                    "prog_name": "matrices",
                },
                {
                    "name": "Шлейфы",
                    "type": "ELECTRIC",
                    "description": "хуйхуйхуйхуйхуй",
                    "image_name": "3b71160fc60290752cb7.jpg",
                    "prog_name": "stubs",
                },
                                {
                    "name": "Платы",
                    "type": "ELECTRIC",
                    "description": "хуйхуйхуйхуйхуй",
                    "image_name": "3b71160fc60290752cb7.jpg",
                    "prog_name": "stubs",
                },
            ],
        )
    db.session.execute(
            insert(Spare),
            [
                {
                    "brand_id": 2,
                    "categ_id": 3,
                    "name": "Digital IXUS 132/IXUS 135",
                    "price": 600,
                    "quantity": 3,
                },
                {
                    "brand_id": 2,
                    "categ_id": 3,
                    "name": "EOS 1D Mark III",
                    "price": 4900,
                    "quantity": 3,
                },
                {
                    "brand_id": 2,
                    "categ_id": 3,
                    "name": "PowerShot A2300/A2400",
                    "price": 500,
                    "quantity": 3,
                },
            ],
        )
    db.session.commit()

class Status(enum.Enum):
    ORDERED = "ordered"
    ACCEPTED = "accepted"
    IN_PROGRESS = "in_progress"
    READY = "ready"
    CLOSED = "closed"


class SocialMediaType(enum.Enum):
    PHONE = "phone"
    EMAIL = "email"
    TG = "tg"
    VK = "vk"


class SpareType(enum.Enum):
    MECHA = "mecha"
    ELECTRIC = "electrical"

class SpareAviability(enum.Enum):
    UNKNOWN = "Уточняйте"
    AVAILABLE = "В наличии"
    UNAVAILABLE = "Отсутствует"

class Admin(UserMixin, db.Model):
    __tablename__ = "admins"
    id: Mapped[int] = mapped_column(primary_key=True)
    username = db.Column(db.String(50), nullable=False)


class RepairOrder(db.Model):
    __tablename__ = "repairs"

    id: Mapped[int] = mapped_column(primary_key=True)
    uniq_link = db.Column(db.String(36), nullable=False, unique=True)
    contact: Mapped[str] = mapped_column()
    social_media_type: Mapped[SocialMediaType] = mapped_column()
    status: Mapped[Status] = mapped_column(default=Status.ORDERED)
    problem: Mapped[str] = mapped_column()
    model = db.Column(db.String(50), nullable=False)
    creation_time = db.Column(
        sqlalchemy.DateTime,
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.now,
    )

    def __repr__(self):
        return f"New order `{self.uniq_link}` from {self.contact} with {self.model}:\n {self.problem}"


class Brand(db.Model):
    __tablename__ = "brand"
    id = mapped_column(Integer, primary_key=True)
    name = db.Column(db.String(256), nullable=False)
    country = db.Column(db.String(2))


class Spare(db.Model):
    __tablename__ = "spares"
    id = mapped_column(Integer, primary_key=True)
    brand_id = mapped_column(Integer, ForeignKey("brand.id"), nullable=False)
    brand = relationship("Brand")
    categ_id = mapped_column(Integer, ForeignKey("spare_category.id"), nullable=False)
    categ = relationship("SpareCategory")
    name = db.Column(db.String(256), nullable=False)
    availability: Mapped[SpareAviability] = mapped_column(default=SpareAviability.UNKNOWN)
    price = db.Column(Integer)
    quantity = db.Column(Integer, default=0)


class SpareCategory(db.Model):
    __tablename__ = "spare_category"
    id = mapped_column(Integer, primary_key=True)
    type: Mapped[SpareType] = mapped_column()
    name = db.Column(db.String(64), nullable=False)
    description = db.Column(db.String(256))
    image_name = db.Column(db.String(30))
    prog_name = db.Column(db.String(30))