import enum
import datetime
import sqlalchemy
from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Integer, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


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

class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)


class Admin(UserMixin, db.Model):
    __tablename__ = "admins"
    id: Mapped[int] = mapped_column(primary_key=True)


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
    brand_id = mapped_column(Integer, ForeignKey("brand.id"))
    brand = relationship("Brand")
    categ_id = mapped_column(Integer, ForeignKey("spare_category.id"))
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


test_spares = [
    Spare(brand_id=1,categ_id=1,name="Digital IXUS 132/IXUS 135",
    availability="В наличии", price=600, quantity=3),
        Spare(brand_id=1,categ_id=1,name="EOS 1D Mark III",
    availability="Уточняйте", price=4900),
        Spare(brand_id=1,categ_id=1,name="PowerShot A2300/A2400",
    availability="Отсутствует", price=500)
]


test_brands = [
    Brand(
        name="Canon"
    ),
    Brand(name="Fujifilm")
]


test_categs = [
    SpareCategory(
        name="Затворы",
        type="mecha",
        description="хуйхуйхуйхуйхуй",
        image_name="3b71160fc60290752cb7.jpg",
        prog_name="shutter"
    ),
    SpareCategory(
        name="Затворы",
        type="electrical",
        description="descdescdescdescdescdescdesc",
        image_name="3b71160fc60290752cb7.jpg",
        prog_name="shutter"
    ),
    SpareCategory(
        name="Матрицы",
        type="electrical",
        description="descdescdescdescdescdescdesc",
        image_name="3b71160fc60290752cb7.jpg",
        prog_name="matrices"
    ),
    SpareCategory(
        name="Шлейфы",
        type="electrical",
        description="descdescdescdescdescdescdesc",
        image_name="3b71160fc60290752cb7.jpg",
        prog_name="stubs"
    ),
]
