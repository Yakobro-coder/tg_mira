from telebot.async_telebot import AsyncTeleBot
from telebot import types
import asyncio

from datetime import datetime
import requests
import json
import logging

from db_foo import select_db, write_db
from filters import admin_filter

from dotenv import dotenv_values


logging.basicConfig(filename='logs/bot_log',
                    format=f"[%(asctime)s] %(levelname)s: \"%(message)s\"",
                    level=logging.INFO)

bot = AsyncTeleBot(dotenv_values('.env').get('TOKEN'))

start_text = "Для авторизации, пожалуйста, укажите <b>ваш логин AMOcrm.</b>"

markup_online = types.ReplyKeyboardMarkup(resize_keyboard=True)
admin_button_markup_online = types.ReplyKeyboardMarkup(resize_keyboard=True)
markup_offline = types.ReplyKeyboardMarkup(resize_keyboard=True)
admin_button_markup_offline = types.ReplyKeyboardMarkup(resize_keyboard=True)

markup_online.add(types.KeyboardButton('Online'))
markup_offline.add(types.KeyboardButton('Offline'))

admin_button_markup_online.row(types.KeyboardButton('Online'))
admin_button_markup_online.row(types.KeyboardButton("/Update_leads"))

admin_button_markup_offline.row(types.KeyboardButton('Offline'))
admin_button_markup_offline.row(types.KeyboardButton("/Update_leads"))


def write_in_log(message):
    logging.info(f"{message.from_user.id} - {message.from_user.first_name} {message.from_user.last_name} \"{message.text}\"")


@bot.message_handler(commands=['start'])
async def start_message(message):
    """
    Start message telegram bot.
    """
    write_in_log(message)
    await bot.send_message(message.chat.id, start_text, parse_mode="HTML")


@bot.message_handler(commands=['Update_leads'])
async def update_lids(message):
    """
    Transport leads for CRM system in status "IN PROGRESS" and back in "NEW LEAD"
    """
    write_in_log(message)
    if admin_filter.check(message):
        token = select_db.get_token()
        headers = {"Authorization": token}
        params = {
            "filter[responsible_user_id]": 8538668,           # Admin8
            "filter[statuses][0][pipeline_id]": 3414178,      #
            "filter[statuses][0][status_id]": 34017646,       # NEW LEAD
            "limit": 250,
            "page": 1
        }

        leads_id = []
        for i in range(5):
            params["page"] = 1 + i
            response = requests.get("https://mirarealestate.amocrm.com/api/v4/leads",
                                    params=params,
                                    headers=headers)

            logging.info(("Params in request:", params, "Status_code:", response.status_code), )

            if response.status_code == 200:
                for lead in response.json().get("_embedded").get("leads"):
                    leads_id.append({"id": lead.get("id"), "status_id": 52806419})
            else:
                break

        # SEND LEADS FOR CRM SYSTEM IN STATUS "IN PROGRESS"
        send_leads_in_progress = requests.patch("https://mirarealestate.amocrm.com/api/v4/leads",
                                                headers=headers,
                                                data=leads_id)

        if send_leads_in_progress.status_code != 200:
            logging.info(("Request:", send_leads_in_progress.text,
                          "Status_code:", send_leads_in_progress.status_code), )
            await bot.send_message(message.chat.id,
                                   "<b>Что то пошло не так. Обратитесь к админу!</b>",
                                   parse_mode="HTML")

        # SEND LEADS FOR CRM SYSTEM IN STATUS "NEW LEAD"
        send_leads_in_new_lead = requests.patch("https://mirarealestate.amocrm.com/api/v4/leads",
                                                headers=headers,
                                                data=leads_id)

        if send_leads_in_new_lead.status_code != 200:
            logging.info(("Request:", send_leads_in_new_lead.text,
                          "Status_code:", send_leads_in_new_lead.status_code), )
            await bot.send_message(message.chat.id,
                                   "<b>Что то пошло не так. Обратитесь к админу!</b>",
                                   parse_mode="HTML")
        else:
            await bot.send_message(message.chat.id,
                                   f"<b>Готово! Было распределено {len(leads_id)} лидов!</b>",
                                   parse_mode="HTML")

# @bot.message_handler(commands=['refreshdatabaseusers'])
# async def refresh_db_user(message):
#     """
#     Cleans writes in database. Command only admins
#     """
#     write_in_log(message)
#     if admin_filter.check(message):
#         write_db.update_users(json.dumps({}))
#         await bot.send_message(message.chat.id,
#                                "Записи по пользователям <b>{telegram_user_id:crm_user_id}</b> сброшены!",
#                                parse_mode="HTML")
#     else:
#         await bot.send_message(message.chat.id,
#                                "<b>Данную команду может выполнять только Админ!</b>",
#                                parse_mode="HTML")


@bot.message_handler(func=lambda message: True, content_types=['text'])
async def registration(message):
    """
    Registration users and write user_id in database.
    """
    write_in_log(message)
    data_base = select_db.all_users()

    if admin_filter.check(message):
        markup_online = admin_button_markup_online
        markup_offline = admin_button_markup_offline

    # search @ (mail) in text, and reg.users
    if '@' in tuple(message.text):
        token = select_db.get_token()
        headers = {"Authorization": token}
        params = {"limit": 250}
        responses = requests.get("https://mirarealestate.amocrm.com/api/v4/users", params=params, headers=headers)

        users = json.loads(responses.text).get('_embedded').get('users')
        users = {user.get('email'): user.get('id') for user in users}

        if message.text in users:
            if data_base.get(str(message.from_user.id)) is None:
                data_base[message.from_user.id] = users.get(message.text)
                write_db.update_users(json.dumps(data_base))
                await bot.send_message(message.chat.id,
                                       "✅Аккаунт авторизован!✅\nДля получения новых лидов, нажмите <b>'Online'</b>.",
                                       parse_mode="HTML",
                                       reply_markup=markup_online)
            elif data_base.get(str(message.from_user.id)) is not None:
                await bot.send_message(message.chat.id, f'Пользователь {message.text} уже Авторизован!')
        else:
            await bot.send_message(message.chat.id,
                                   f'Пользователь {message.text} не существует в AMOcrm!🤔\n'
                                   f'Необходимо пройти Авторизацию!\nПожалуйста, укажите <b>ваш логин AMOcrm.</b>',
                                   parse_mode="HTML")

    # Change status in crm system for registered users in bot.
    elif message.text == 'Online' and data_base.get(str(message.from_user.id)) is not None:
        crm_user_id = data_base.get(str(message.from_user.id))
        data = {"status": 1}
        requests.post(
            f"https://widgets.comf5.ru/crm/28844278/{crm_user_id}/Respool/6032/setStatus?token={dotenv_values('.env').get('WIDGET_TOKEN')}",
            data=data)
        await bot.send_message(message.chat.id,
                               "🔥Поздравляю, вы <b>'Online'</b>!🔥\nТеперь вы можете получать новые лиды.",
                               parse_mode="HTML",
                               reply_markup=markup_offline)

    elif message.text == 'Offline' and data_base.get(str(message.from_user.id)) is not None:
        crm_user_id = data_base.get(str(message.from_user.id))
        data = {"status": 0}
        requests.post(
            f"https://widgets.comf5.ru/crm/28844278/{crm_user_id}/Respool/6032/setStatus?token={dotenv_values('.env').get('WIDGET_TOKEN')}",
            data=data)
        await bot.send_message(message.chat.id,
                               "⛔️Внимание вы <b>'Offline'</b>!⛔️\nТеперь вы не можете получать новые лиды!",
                               parse_mode="HTML",
                               reply_markup=markup_online)

    # Processing left messages not according to the script
    elif '@' not in tuple(message.text):
        if data_base.get(str(message.from_user.id)) is not None:
            await bot.send_message(message.chat.id,
                                   '<b>Ошибка: текст не принимаем. Жмите на кнопку😉</b>',
                                   parse_mode="HTML")
        elif data_base.get(str(message.from_user.id)) is None:
            await bot.send_message(message.chat.id,
                                   '<b>Ошибка: Необходимо пройти авторизации!\nНажмите команду /start</b>',
                                   parse_mode="HTML")


asyncio.run(bot.polling(none_stop=True))
