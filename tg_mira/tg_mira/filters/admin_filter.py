from tg_mira.tg_mira.models import *


def check(message):
    return int(message.chat.id) in Admin.ADMIN.value
