from . import db_connect
from sqlalchemy import exc


def update_users(json_users, connection=db_connect.connect()):
    try:
        connection.execute("UPDATE bot_mira "
                           "SET safe=%s"
                           "WHERE id=2;", (json_users,))
    except exc.SQLAlchemyError as e:
        error = str(e.__dict__['orig'])
        print(error)
