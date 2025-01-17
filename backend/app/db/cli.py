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