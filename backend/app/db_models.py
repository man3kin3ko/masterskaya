import enum
from uuid import uuid4
import datetime
import sqlalchemy
from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


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


class Base(DeclarativeBase):
    type_annotation_map = {
        Status: sqlalchemy.Enum(Status, length=50, native_enum=False, default=Status.ORDERED),
        SocialMediaType: sqlalchemy.Enum(SocialMediaType, length=6, native_enum=False)
    }


db = SQLAlchemy(model_class=Base)


class Admin(UserMixin, db.Model):
    __tablename__ = "admins"
    id: Mapped[int] = mapped_column(primary_key=True)


class RepairOrder(db.Model):
    __tablename__ = "repairs"

    id: Mapped[int] = mapped_column(primary_key=True)
    uniq_link = db.Column(db.String(36), nullable=False, unique=True)
    contact: Mapped[str] = mapped_column()
    social_media_type: SocialMediaType = mapped_column()
    status: Status = mapped_column(default=Status.ORDERED)
    problem: Mapped[str] = mapped_column()
    model = db.Column(db.String(50), nullable=False)
    creation_time = db.Column(sqlalchemy.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.now)

    def __init__(self, **kwargs):
        if 'uniq_link' not in kwargs:
            kwargs['uniq_link'] = uuid4()
        super().__init__(**kwargs)

    def __repr__(self):
        return f"New order `{self.uniq_link}` from {self.contact} with {self.model}:\n {self.problem}"