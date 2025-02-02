import click
from app.db import DBProxy
from app.db.cli import *

from pwd import getpwnam
from grp import getgrnam
from os import chown

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
    pass

@cli.command("restore-db")
def restore_db_command():
    pass

if __name__ == '__main__':
    cli()