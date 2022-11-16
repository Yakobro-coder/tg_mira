from . import db_connect


def get_token(connection=db_connect.connect()):
    token = connection.execute("SELECT access_token FROM tokens WHERE id=5").fetchall()[0][0]
    return str(token)


def all_users(connection=db_connect.connect()):
    try:
        users = connection.execute("SELECT safe FROM bot_mira WHERE id=1").fetchall()[0][0]
        return users
    except IndexError as ex:
        return 'ERROR: "' + str(ex) + '". Database is clear! Need to add "{}" to the database.'
