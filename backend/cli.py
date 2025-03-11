import click
from pwd import getpwnam
from grp import getgrnam
from os import chown

from app.db import DBProxy
from app.db.cli import *

db_proxy = DBProxy()

@click.group()
def cli():
    pass

@cli.command("init-db")
def init_db_command():
    db_proxy.create_tables()
    session = db_proxy.create_session()
    init_db(session)

    chown(db_proxy.filename, getpwnam("www-data").pw_uid, getgrnam("www-data").gr_gid)

@cli.command("dump-db")
def dump_db_command():
    session = db_proxy.create_session() # TODO utils
    dump_db(session)

@cli.command("drop-table")
@click.option('--table')
def drop_table_command(table):
    drop_table(db_proxy.engine, table)

@cli.command("create-table")
@click.option('--table')
def create_table_command(table):
    create_table(db_proxy.engine, table)


@cli.command("update-table")
@click.option('--table')
@click.option('--path', default=None)
def update_table_command(table, path):
    if not path:
        path = table + ".csv"

    session = db_proxy.create_session()
    update_table(session, table, path)
    
@cli.command("insert-table")
@click.option('--table')
@click.option('--path', default=None)
def insert_table_command(table, path):
    if not path:
        path = table + ".csv"

    session = db_proxy.create_session()
    insert_table(session, table, path)

if __name__ == '__main__':
    cli()