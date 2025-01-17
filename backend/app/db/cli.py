from sqlalchemy import insert
from .models import *

def init_db(session):
    session.execute(
            insert(Brand),
            [
                {"name": "Kodak", "country": "US"},
                {"name": "Canon", "country": "JP"},
                {"name": "Fujifilm", "country": "JP"},
                {"name": "Nikon", "country": "JP"},
                {"name": "Sony", "country": "JP"},
                {"name": "Sigma", "country": "JP"},
                {"name": "Pentax", "country": "JP"}
            ],
        )
    session.execute(
            insert(MechanicalSpare),
            [
                {
                    "name": "Затворы",
                    "description": "Центральный затвор - это сердце фотоаппарата",
                    "slug": "shutter",
                }
            ])
    session.execute(
            insert(ElectricalSpare),
            [
                {
                    "name": "Платы и матрицы",
                    "description": "Разборка и реплики",
                    "slug": "matrices",
                },
                {
                    "name": "Шлейфы",
                    "description": "Гибкие платы для матриц, дисплеев и кнопок панелей управления",
                    "slug": "stubs",
                },
                {
                    "name": "Микросхемы",
                    "description": "Транзисторы, контроллеры, процессоры",
                    "slug": "chips",
                },
                {
                    "name": "Вспышки",
                    "description": "Встроенные вспышки и лампы",
                    "slug": "flash",
                },
                {
                    "name": "Двигатели",
                    "description": "Микромоторы затворов и объективов",
                    "slug": "motor",
                },
                {
                    "name": "Mirror box",
                    "description": "DSLR, SLT и DSLT",
                    "slug": "mirror_box",
                },
                {
                    "name": "Затворы",
                    "description": "Контролируют светочувствительность матрицы",
                    "slug": "shutter",
                },
                {
                    "name": "Части корпуса",
                    "description": "Кнопки, рычаги, крышки и накладки",
                    "slug": "case",
                },
                {
                    "name": "Ламели и шестерни",
                    "description": "А также конденсаторы, подшипники, байонеты и другие запчасти",
                    "slug": "stuff",
                },
                {
                    "name": "Встраиваемые объективы",
                    "description": "",
                    "slug": "lens",
                },
            ],
        )
    session.execute(
            insert(Spare),
            [
                {
                    "brand_id": 2,
                    "category_id": 3,
                    "name": "Digital IXUS 132/IXUS 135",
                    "price": 600,
                    "quantity": 3,
                },
                {
                    "brand_id": 2,
                    "category_id": 3,
                    "name": "EOS 1D Mark III",
                    "price": 4900,
                    "quantity": 3,
                },
                {
                    "brand_id": 2,
                    "category_id": 3,
                    "name": "PowerShot A2300/A2400",
                    "price": 500,
                    "quantity": 3,
                },
            ],
        )
    session.commit()