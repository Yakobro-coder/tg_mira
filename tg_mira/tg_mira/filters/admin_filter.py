from tg_mira.models.users_model import Admin


def check(message):
    return int(message.chat.id) in Admin.ADMIN.value
