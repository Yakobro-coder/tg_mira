from models import *


def check(message):
    return int(message.chat.id) in Admin.ADMIN.value
