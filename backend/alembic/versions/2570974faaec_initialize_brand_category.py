"""Initialize Brand & Category

Revision ID: 2570974faaec
Revises: 
Create Date: 2025-12-20 15:46:41.141262

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from app.db.models import *


# revision identifiers, used by Alembic.
revision: str = '2570974faaec'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


BRANDS = [
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
        {"name": "Conica", "country": "JP"},
        {"name": "Ricoh", "country": "JP"},
    ]

MECHANICAL_SPARES = [
        {
            "name": "Затворы",
            "description": "Центральный затвор - это сердце фотоаппарата",
            "slug": "shutter",
        }
    ]

ELECTRICAL_SPARES = [
        {
            "name": "Платы и матрицы",
            "description": "Разборка и реплики",
            "slug": "matrices",
            "image_name":"matrix.png"
        },
        {
            "name": "Шлейфы",
            "description": "Гибкие платы для матриц, дисплеев и кнопок панелей управления",
            "slug": "stubs",
            "image_name":"stub.png"
        },
        {
            "name": "Микросхемы",
            "description": "Транзисторы, контроллеры, процессоры",
            "slug": "chips",
            "image_name":"chips.png"
        },
        {
            "name": "Вспышки",
            "description": "Встроенные вспышки и лампы",
            "slug": "flash",
            "image_name":"flash.png"
        },
        {
            "name": "Двигатели",
            "description": "Микромоторы затворов и объективов",
            "slug": "motor",
            "image_name":"motor.png"
        },
        {
            "name": "Mirror box",
            "description": "DSLR, SLT и DSLT",
            "slug": "mirror_box",
            "image_name":"mirror_box.png"
        },
        {
            "name": "Затворы",
            "description": "Контролируют светочувствительность матрицы",
            "slug": "shutter",
            "image_name":"shutter_electric.png"
        },
        {
            "name": "Части корпуса",
            "description": "Кнопки, рычаги, крышки и накладки",
            "slug": "case",
            "image_name":"case.png"
        },
        {
            "name": "Ламели и шестерни",
            "description": "А также конденсаторы, подшипники, байонеты и другие запчасти",
            "slug": "stuff",
            "image_name":"lamel.png"
        },
        {
            "name": "Встраиваемые объективы",
            "description": "",
            "slug": "lens",
            "image_name":"lens.png"
        },
    ]


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    def is_empty(table, session):
        return session.query(table).first() is None

    def init_table(table, datalist):
        # print(str(table)) <class 'app.db.models.Brand'>
        # if str(table) not in inspector.get_table_names():
        
        session = sa.orm.sessionmaker()(bind=conn)
        if is_empty(table, session):
            session.execute(insert(table), datalist)
            session.commit()

    init_table(Brand, BRANDS)
    init_table(MechanicalSpareCategory, MECHANICAL_SPARES)
    init_table(ElectricalSpareCategory, ELECTRICAL_SPARES)


def downgrade() -> None:
    """Downgrade schema."""
    pass
