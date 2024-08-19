from sqlalchemy import insert
from .models import Brand, SpareCategory, Spare

def init_db(db):
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