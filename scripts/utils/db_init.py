# Recreate empty DB tables

import sqlalchemy as sa
from sqlalchemy_utils import database_exists, create_database

from app import context
from app.models import Base


def __init_db():
    engine = sa.create_engine(context.db_config.db_con_string,
                              echo=False,
                              encoding='utf-8')
    if not database_exists(engine.url):
        create_database(engine.url)
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)


if __name__ == '__main__':
    if input(
            'Are you sure you want to recreate database? (y/N) '
    ).lower() == 'y':
        __init_db()
