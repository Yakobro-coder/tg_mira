from . import db_connect
from sqlalchemy import exc
import logging
from dotenv import dotenv_values


def update_users(json_users, connection=db_connect.connect()):
    try:
        connection.execute("UPDATE bot_mira "
                           "SET safe=%s"
                           f"WHERE id={dotenv_values('.env').get('ID_IN_DB')};", (json_users,))
    except exc.SQLAlchemyError as e:
        error = str(e.__dict__['orig'])
        logging.info(error)


def add_data(model):
    try:
        session = db_connect.get_session()
        session.add(model)
        session.commit()
    except exc.SQLAlchemyError as e:
        error = str(e.__dict__['orig'])
        logging.info(error)
