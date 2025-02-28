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
        #if not table().is_empty(session): causes weird shit sir plz investigate
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
            insert(MechanicalSpareCategory),
            [
                {
                    "name": "Затворы",
                    "description": "Центральный затвор - это сердце фотоаппарата",
                    "slug": "shutter",
                }
            ])
    session.execute(
            insert(ElectricalSpareCategory),
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
    session.commit()