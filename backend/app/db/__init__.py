from .models import *

import logging
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from app.utils import Singleton

# присрать интеграцию с alembic (в принципе можно руками прост на будущее)
# pagination
# https://stackoverflow.com/questions/74520043/flask-pagination-without-sqlalchemy
# https://stackoverflow.com/questions/13258934/applying-limit-and-offset-to-all-queries-in-sqlalchemy


class DBProxy(metaclass=Singleton): #
    def __init__(self, engine_uri='sqlite:///database.db', max_per_page=5):
        self.max_per_page = max_per_page

        self.engine = create_engine(engine_uri)
        self._make_session = sessionmaker(bind=self.engine)
        self._pending_operations = []

    def create_tables(self, base_model=Base):
        base_model.metadata.create_all(self.engine)

    def create_session(self):
        return self._make_session()

    def add_to_transaction(self, f):
        self._pending_operations.append(f)

    def execute_in_context(self):
        with self._make_session() as s:
            try:
                [f(s) for f in self._pending_operations]
            except:
                s.rollback()
                raise
            else:
                s.commit()
                self._pending_operations = []


### categories queries ###

def categories(session):
    return session.query(SpareCategory).all()

def categories_page(session, page, max_per_page=4):
    query = session.query(SpareCategory)
    return query.limit(max_per_page).offset((int(page) - 1) * max_per_page)

def category_by_id(session, subtype, category_id):
    subtype_class = SpareCategory.from_discriminator(subtype)

    return session.query(subtype_class).where(subtype_class.id == category_id).one()

def category_by_slug(session, subtype, slug):
    subtype_class = SpareCategory.from_discriminator(subtype)

    return session.query(subtype_class).where(subtype_class.slug == slug).one()

### spare queries ###

def spare(session, spare_id):
    return session.query(Spare).where(Spare.id == int(spare_id)).one()

def spares_by_category_and_brand(session, brand, category):
    q = session.query(Spare).where(Spare.brand_id == brand.id)
    q = q.where(Spare.category_id == category.id)

    #q = q.where(Spare.name == spare.name) ???
    return q.all()

def spares_by_subtype_and_slug(session, subtype, slug):
    subtype_class = SpareCategory.from_discriminator(subtype)
    return session.query(subtype_class).where(subtype_class.slug == slug).one().spares

### repair queries ###

def is_repair_order_exist(uuid):
    return session.query(exists().where(RepairOrder.uuid == uuid)).scalar()

def repair_order_by_uuid(session, uuid):
    return session.query(RepairOrder).where(RepairOrder.uuid == uuid).one()

def repair_orders_page_by_master(session, master_id, page=1, max_per_page=4):
    query = session.query(RepairOrder).where(RepairOrder.master_id == master_id)
    query_limit = query.limit(max_per_page).offset((int(page) - 1) * max_per_page)

    return query_limit.all()

### brand queries ###

def brand_by_name(session, name):
    return session.query(Brand).where(Brand.name == name).one()