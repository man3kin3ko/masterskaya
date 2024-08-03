import enum
import datetime
import sqlalchemy
import csv
from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Integer, ForeignKey, select, insert, update
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

def get_spares(spare_category_id):
    return db.session.execute(
        select(Spare)
        .join(Spare.brand)
        .join(Spare.categ)
        .where(SpareCategory.id == spare_category_id)
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

def get_categ(categ_id):
    return db.session.execute(
        select(SpareCategory.name).where(SpareCategory.id == int(categ_id))
    ).first()

def export_csv(categ_id):
    records = db.session.execute(
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

def get_categs_page(max_per_page, page):
    return db.session.query(SpareCategory.id, SpareCategory.name).paginate(page=int(page), max_per_page=int(max_per_page))

def get_repair_order(uuid): # add time when accepted on status page
    return db.session.execute(
        select(RepairOrder).where(RepairOrder.uniq_link == str(uuid))
    ).first()[0]

def get_repair_order_full(uuid):
    return db.session.execute(
        select(RepairOrder.model, RepairOrder.status, RepairOrder.last_modified_time, RepairOrder.problem, RepairOrder.social_media_type, RepairOrder.contact)
        .where(RepairOrder.uniq_link == uuid)
    ).first()

def is_repair_order_exists(uuid):
    return db.session.execute(
        select(RepairOrder.uniq_link).where(RepairOrder.uniq_link == str(uuid))
    ).first()

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

def update_repair_status(uuid, status, master_id):
    db.session.execute(
        update(RepairOrder)
        .where(RepairOrder.uniq_link == uuid)
        .values(status=Status(status).name, master_id=master_id)
    )
    db.session.commit()

def get_order_page(max_per_page, page, master_id):
    return db.session.query(RepairOrder.uniq_link, RepairOrder.problem, RepairOrder.model).where(RepairOrder.master_id == master_id).paginate(page=int(page), max_per_page=int(max_per_page))

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
                    "description": "Центральный затвор - это сердце фотоаппарата",
                    "image_name": "test_categ1.png",
                    "prog_name": "shutter",
                },
                {
                    "name": "Платы и матрицы",
                    "type": "ELECTRIC",
                    "description": "Разборка и реплики",
                    "image_name": "3b71160fc60290752cb7.jpg",
                    "prog_name": "matrices",
                },
                {
                    "name": "Шлейфы",
                    "type": "ELECTRIC",
                    "description": "Гибкие платы для матриц, дисплеев и кнопок панелей управления",
                    "image_name": "3b71160fc60290752cb7.jpg",
                    "prog_name": "stubs",
                },
                {
                    "name": "Микросхемы",
                    "type": "ELECTRIC",
                    "description": "Транзисторы, контроллеры, процессоры",
                    "image_name": "3b71160fc60290752cb7.jpg",
                    "prog_name": "chips",
                },
                {
                    "name": "Вспышки",
                    "type": "ELECTRIC",
                    "description": "Встроенные вспышки и лампы",
                    "image_name": "3b71160fc60290752cb7.jpg",
                    "prog_name": "flash",
                },
                {
                    "name": "Двигатели",
                    "type": "ELECTRIC",
                    "description": "Миктромоторы затворов и объективов",
                    "image_name": "3b71160fc60290752cb7.jpg",
                    "prog_name": "motor",
                },
                {
                    "name": "Mirror box",
                    "type": "ELECTRIC",
                    "description": "DSLR, SLT и DSLT",
                    "image_name": "3b71160fc60290752cb7.jpg",
                    "prog_name": "mirror_box",
                },
                {
                    "name": "Затворы",
                    "type": "ELECTRIC",
                    "description": "Контролируют светочувствительность матрицы",
                    "image_name": "test_categ2.png",
                    "prog_name": "shutter",
                },
                {
                    "name": "Части корпуса",
                    "type": "ELECTRIC",
                    "description": "Кнопки, рычаги, крышки и накладки",
                    "image_name": "3b71160fc60290752cb7.jpg",
                    "prog_name": "case",
                },
                {
                    "name": "Ламели и шестерни",
                    "type": "ELECTRIC",
                    "description": "А также конденсаторы, подшипники, байонеты и другие запчасти",
                    "image_name": "3b71160fc60290752cb7.jpg",
                    "prog_name": "stuff",
                },
                {
                    "name": "Объективы",
                    "type": "ELECTRIC",
                    "description": "Встроенные в качестве запчастей",
                    "image_name": "3b71160fc60290752cb7.jpg",
                    "prog_name": "lens",
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
    PROBLEMS = "problem"
        

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


class RepairOrder(db.Model):
    __tablename__ = "repairs"

    id: Mapped[int] = mapped_column(primary_key=True)
    uniq_link = db.Column(db.String(36), nullable=False, unique=True)
    contact: Mapped[str] = mapped_column()
    social_media_type: Mapped[SocialMediaType] = mapped_column()
    status: Mapped[Status] = mapped_column(default=Status.ORDERED)
    problem: Mapped[str] = mapped_column()
    model = db.Column(db.String(50), nullable=False)
    last_modified_time = db.Column(
        sqlalchemy.DateTime,
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.now,
    )
    master_id: Mapped[int] = mapped_column(nullable=True)

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