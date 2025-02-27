import csv
from app.utils import BaseEnum, flatten_lists
from abc import abstractmethod

class DBDeserializer:
    def __init__(self, session):
        self.session = session

    def query_table(self, table, path, sql_clause):
        with open(path) as f:
            reader = csv.DictReader(f)
            self.session.execute(sql_clause(table), [table.deserialize(row) for row in reader])
            self.session.commit()


class SerializableMixin():
    @staticmethod
    @abstractmethod
    def deserialize(row):
        return row

    @classmethod
    def serialize(cls, session):
        assert cls.__name__ != SerializableMixin.__name__, "Only for child classes"

        table = session.query(cls).order_by(cls.id.asc()).all()
        rows = []
        for record in table:
            rows.append(list(map(
                    lambda x: x.name if issubclass(x.__class__, BaseEnum) else x, 
                    [ getattr(record, i.name, None) for i in cls.__mapper__.columns ]
                )))
        return rows

    @classmethod
    def get_csv_header(cls):
        assert cls.__name__ != SerializableMixin.__name__, "Only for child classes" # TODO: move to utils

        # cls.__mapper__.all_orm_descriptors.keys() for unions?
        return [i.key for i in cls.__mapper__.columns]

    @staticmethod
    def get_serializables():
        # https://stackoverflow.com/questions/29994618/classmethod-property-typeerror-property-object-is-not-iterable # TODO: utils
        def f(cls):
            if not len(cls.__subclasses__()):
                return [cls]
            return [cls] + flatten_lists([f(i) for i in cls.__subclasses__()])
            
        return flatten_lists([f(i) for i in SerializableMixin.__subclasses__()])

    @classmethod
    def dump(cls, session):
        filename = cls.__name__ + ".csv"
        with open(filename, 'w') as f: # + sep dir
            writer = csv.writer(f)
            writer.writerow(cls.get_csv_header())
            writer.writerows(cls.serialize(session))