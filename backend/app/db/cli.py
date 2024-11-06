import csv
from sqlalchemy import insert, select, update
from .models import Brand, SpareCategory, Spare, RepairOrder, BaseEnum, CameraResale

tables = [RepairOrder, SpareCategory, Spare, Brand]

def dump_db(db, tables=tables):
    for i in tables:
        records = db.session.execute(
            select(i)
        ).all()
        with open(f'instance/{i.__name__}.csv', 'w') as f:
            writer = csv.writer(f)
            writer.writerow(i.get_header())
            for record in records:
                writer.writerow(i.serialize(record)) 

def restore_db(db, tables=tables):
    for i in tables:
        with open(f'instance/{i.__name__}.csv') as f:
            reader = csv.reader(f)
            header = next(reader)
            db.session.execute(
                    update(i), [i.from_csv(dict(zip(header, row))) for row in reader]
                )
            db.session.commit()


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
                    "description": "Микромоторы затворов и объективов",
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
    db.session.execute(
        insert(CameraResale), [
            {
                "name":"Minolta Hi-matic E",
                "avito_link":"https://www.avito.ru/sankt-peterburg/fototehnika/minolta_hi-matic_e_4523545837",
                "description":"Дальномерный фотоаппарат с светосильным роккором 1.7. Проведено обслуживание, отснята тестовая пленка.",
                "price":10000,
                "_images":"https://90.img.avito.st/image/1/1.fNXzvLa40DzFFRI5h9Ul5csd0jpNHVI0hRjSPkMV2DZF.ert6Df24Ht-gz_8S-lbkkBdJMdxSTPcx-MEcX5bNoqU,https://70.img.avito.st/image/1/1.Ovgo-ra4lhEeU1QUULoSzxBblBeWWxQZXl6UE5hTnhue.Xjo7BPU8VFcBgIOBWvQnZbpaF0CPso0aHq9XetVP8sw"
            },
            {
                "name":"Cosina CX-1",
                "avito_link":"https://www.avito.ru/sankt-peterburg/fototehnika/cosina_cx-1_4332148650",
                "description":"Редкая Cosina CX-1 в рабочем состоянии с новыми прокладками и тестами на 50(просрочка самсунга) и 400 (ilford delta 400) ISO.\nБатарейки в комплекте",
                "price":13000,
                "_images":"https://60.img.avito.st/image/1/1.d3QiTba4250U5BmYQERDLEHv2Zuc7FmVVOnZn5Lk05eU.duIh7tUF0bVcElZl2aw-w-lnbVPk92nO6YYqGggeltQ,https://70.img.avito.st/image/1/1.ZbgM3ba4yVE6dAtUStRR4G9_y1eyfEtZennLU7x0wVu6.jutx8dVnlnWfTDdL14IyewyB8nNQJ-tER7OXXr482mE,https://80.img.avito.st/image/1/1.Y6VfWra4z0xp8w1JFVNX_Tz4zUrh-01EKf7NTu_zx0bp.BlQ2DEzDRLOA4JPnq0OWfenUUctVI-rXMTDZHZM8vuk"
            },
            {
                "name":"Canon 70 zoom",
                "avito_link":"https://www.avito.ru/sankt-peterburg/fototehnika/canon_70_zoom_4331841907",
                "description":"Canon sureshot 70 zoom, достойная мылка с зумом, вспышка и затвор в порядке, небольшая коцка на пластиковой морде объектива.",
                "price":5000,
                "_images":"https://30.img.avito.st/image/1/1.zNhsNra4YDFan6I0eHWesw-UYjfSl-I5GpJiM9yfaDva.3TrZrSxiYy3RzBs7IdWyeMnWbOG_uFEXICK0ubszJV0,"
            }
        ]
    )
    db.session.commit()