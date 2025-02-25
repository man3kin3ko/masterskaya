from sqlalchemy import insert, update
from app.db.models import *
from app.db.serialization import SerializableMixin, DBDeserializer

def insert_table(session, table_name, path):
    for table in SerializableMixin.get_serializables():
        if table.__name__ == table_name:
            helper = DBDeserializer(session)
            helper.query_table(table, path, insert)

def update_table(session, table_name, path):
    for table in SerializableMixin.get_serializables():
        if table.__name__ == table_name:
            helper = DBDeserializer(session)
            helper.query_table(table, path, update)

def dump_db(session):
    for table in SerializableMixin.get_serializables():
        if not table.is_empty():
            table.dump(session)

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
                {"name": "Conica", "country": "JP"},
                {"name": "Ricoh", "country": "JP"},
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
            ]
        )
    session.execute(
        insert(CommonSpare),
        [{
            "name": "Элементы питания",
            "description":"",
            "slug":"battery"
        }]
    )
    # session.execute(
    #         insert(Spare),
    #         [
    #             {
    #                 "brand_id": 21,
    #                 "category_id": 3,
    #                 "name": "R1s",
    #                 "price": 1500,
    #                 "quantity": 4,
    #                 "availability": "available"
    #             },
    #             {
    #                 "brand_id": 2,
    #                 "category_id": 3,
    #                 "name": "Mark II",
    #                 "price": 3500,
    #                 "quantity": 1,
    #                 "availability": "available"
    #             },
    #             {
    #                 "brand_id": 20,
    #                 "category_id": 3,
    #                 "name": "Big Mini",
    #                 "price": 1500,
    #                 "quantity": 4,
    #                 "availability": "available"
    #             },
    #             {
    #                 "category_id": 12,
    #                 "name": "Элемент ртутно-цинковый рц-53",
    #                 "price": 320,
    #                 "quantity": 100,
    #                 "availability": "available"
    #             },
    #         ],
    #     )
    # session.execute(
    #     insert(ResaleCamera),
    #     [
    #         {
    #             "id": 1,
    #             "name" : "Konica C35 EL",
    #             "description" : "Тестовая позиция. Нет в наличии.",
    #             "price" : 6000,
    #             "quantity": 0
    #         },
    #         {
    #             "id": 2,
    #             "name" : "Rollei 35S",
    #             "description" : "Тестовая позиция. Нет в наличии.",
    #             "price" : 25000,
    #             "quantity": 0
    #         },
    #         {
    #             "id": 3,
    #             "name" : "Minolta Hi-matic E",
    #             "description" : "Тестовая позиция. Нет в наличии.",
    #             "price" : 9200,
    #             "quantity": 0
    #         },
    #     ]
    # )
    # session.execute(
    #     insert(ResaleImage),
    #     [
    #         {
    #             "resale_id": "1",
    #             "external_url":"https://00.img.avito.st/image/1/1.TfjKKba44RH8gCMU3EA5yPKI4xd0iGMZvI3jE3qA6Rt8.2Fy4mm11VO6h_8BYvpN1GTp2ceaHmBiLeGaUyz-p4BM"
    #         },
    #         {
    #             "resale_id": "1",
    #             "external_url":"https://10.img.avito.st/image/1/1.xqiDMra4akG1m6hEgzG4mLuTaEc9k-hJ9ZZoQzObYks1.JGrvzO1Hgsva-89VHv0uzhaOhAv79zRDvlqUKwmmNdA"
    #         },
    #         {
    #             "resale_id": "2",
    #             "external_url":"https://00.img.avito.st/image/1/1.ZLQ6Jra4yF0MjwpYfn88hRSHyluEh0pVTILKX4qPwFeM.xo0ySkxGGd17-WkLOU03luNVxPgK9cOWeieReM2LRQM"
    #         },
    #         {
    #             "resale_id": "2",
    #             "external_url":"https://70.img.avito.st/image/1/1.H-wmbLa4swUQxXEAFBhmsADNsQOYzTENUMixB5bFuw-Q.yrCF_ydBvs3oxZaIduCD8QODhlptLAZBsokBMJCAC8E"
    #         },
    #         {
    #             "resale_id": "2",
    #             "external_url":"https://90.img.avito.st/image/1/1.3P4oqba4cBceALISHOqvog4IchGWCPIfXg1yFZgAeB2e.LdGK7qQhyYMC5x5sCW8nkN9rjsGFFmEDDvvfQ-kQs78"
    #         },
    #         {
    #             "resale_id": "3",
    #             "external_url":"https://90.img.avito.st/image/1/1.fNXzvLa40DzFFRI5h9Ul5csd0jpNHVI0hRjSPkMV2DZF.ert6Df24Ht-gz_8S-lbkkBdJMdxSTPcx-MEcX5bNoqU"
    #         },
    #         {
    #             "resale_id": "3",
    #             "external_url":"https://70.img.avito.st/image/1/1.Ovgo-ra4lhEeU1QUULoSzxBblBeWWxQZXl6UE5hTnhue.Xjo7BPU8VFcBgIOBWvQnZbpaF0CPso0aHq9XetVP8sw"
    #         }
    #     ]
    # )
    session.commit()