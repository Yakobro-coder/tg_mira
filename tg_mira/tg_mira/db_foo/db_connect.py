

import sqlalchemy
from sqlalchemy.orm import sessionmaker
from dotenv import dotenv_values


def connect():
    settings = dotenv_values('.env')
    db = f"postgresql://{settings.get('POSTGRES_USER')}:{settings.get('POSTGRES_PASSWORD')}@{settings.get('HOST')}:5432/{settings.get('POSTGRES_NAME_DATABASE')}"
    engine = sqlalchemy.create_engine(db)
    connection = engine.connect()

    return connection


def get_session():
    Session = sessionmaker(bind=_get_engine())
    session = Session()

    return session


def _get_engine():
    settings = dotenv_values('.env')
    db = f"postgresql://{settings.get('POSTGRES_USER')}:{settings.get('POSTGRES_PASSWORD')}@{settings.get('HOST')}:5432/{settings.get('POSTGRES_NAME_DATABASE')}"
    engine = sqlalchemy.create_engine(db)

    return engine


def get_metadata():
    metadata = sqlalchemy.MetaData(bind=_get_engine())

    return metadata
