import sqlalchemy
from dotenv import dotenv_values


def connect():
    settings = dotenv_values('.env')
    db = f"postgresql://{settings.get('POSTGRES_USER')}:{settings.get('POSTGRES_PASSWORD')}@{settings.get('HOST')}:5432/{settings.get('POSTGRES_NAME_DATABASE')}"
    engine = sqlalchemy.create_engine(db)
    connection = engine.connect()

    return connection
