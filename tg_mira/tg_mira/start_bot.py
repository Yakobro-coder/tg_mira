from telebot.async_telebot import AsyncTeleBot
from telebot import types
from models import *
import asyncio

from datetime import datetime
import pytz
import requests
import json
import logging

from db_foo import select_db, write_db
from filters import admin_filter

from dotenv import dotenv_values

tmz = pytz.timezone(dotenv_values('.env').get('TIMEZONE'))

logging.basicConfig(filename='logs/bot_log', format=f"%(levelname)s: %(message)s", level=logging.INFO)

bot = AsyncTeleBot(dotenv_values('.env').get('TOKEN'))

start_text = "Для авторизации, пожалуйста, укажите <b>ваш логин AMOcrm.</b>"


def write_in_log(message):
    logging.info(f"[{datetime.now(tmz)}] {message.from_user.id} - {message.from_user.first_name} {message.from_user.last_name} \"{message.text}\"")


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
            "filter[responsible_user_id]": 8538668,           # admin8:8538668    admin:7539577
            "filter[statuses][0][pipeline_id]": 3414178,      # Registered Leads
            "filter[statuses][0][status_id]": 34017646,       # NEW LEAD
            "limit": 250,
            "page": 1
        }

        leads_id = []
        for i in range(5):
            params["page"] = 1 + i
            response_leads = requests.get("https://mirarealestate.amocrm.com/api/v4/leads",
                                          params=params,
                                          headers=headers)

            logging.info(("Params in request:", params, "Status_code:", response_leads.status_code), )

            if response_leads.status_code == 200:
                for lead in response_leads.json().get("_embedded").get("leads"):
                    leads_id.append({"id": lead.get("id"), "status_id": 52806419})
            else:
                break

        # SEND LEADS FOR CRM SYSTEM IN STATUS "IN PROGRESS"
        send_leads_in_progress = requests.patch("https://mirarealestate.amocrm.com/api/v4/leads",
                                                headers=headers,
                                                data=json.dumps(leads_id))

        if send_leads_in_progress.status_code != 200:
            logging.info(("Request:", send_leads_in_progress.text,
                          "Status_code:", send_leads_in_progress.status_code), )

        # SEND LEADS FOR CRM SYSTEM IN STATUS "NEW LEAD"
        [lead.update(status_id=34017646) for lead in leads_id]
        send_leads_in_new_lead = requests.patch("https://mirarealestate.amocrm.com/api/v4/leads",
                                                headers=headers,
                                                data=json.dumps(leads_id))

        if send_leads_in_new_lead.status_code != 200:
            logging.info(("Request:", send_leads_in_new_lead.text,
                          "Status_code:", send_leads_in_new_lead.status_code), )
            if response_leads.status_code == 204 and send_leads_in_progress.status_code == 400 and send_leads_in_new_lead.status_code == 400:
                await bot.send_message(message.chat.id,
                                       "<b>Автоматическое распределение выполнено!♻\n"
                                       "Лидов для распределения не найдено!</b>",
                                       parse_mode="HTML")
            else:
                await bot.send_message(message.chat.id,
                                       "<b>Что то пошло не так. Обратитесь к админу!!!</b>",
                                       parse_mode="HTML")
        else:
            word = ""
            if len(leads_id) == 1:
                word = "лид"
            elif 1 < len(leads_id) < 5:
                word = "лидa"
            elif 4 < len(leads_id) or len(leads_id) == 0:
                word = "лидов"

            await bot.send_message(message.chat.id,
                                   f"<b>Готово! Распределено: {len(leads_id)} {word}!</b>",
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
    #CREATE BUTTON
    markup_online = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup_online.add(types.KeyboardButton('🟢Online'))

    admin_button_markup_online = types.ReplyKeyboardMarkup(resize_keyboard=True)
    admin_button_markup_online.row(types.KeyboardButton('🟢Online'))
    admin_button_markup_online.row(types.KeyboardButton("/Update_leads"))

    markup_offline = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup_offline.add(types.KeyboardButton('🔴Offline'))

    admin_button_markup_offline = types.ReplyKeyboardMarkup(resize_keyboard=True)
    admin_button_markup_offline.row(types.KeyboardButton('🔴Offline'))
    admin_button_markup_offline.row(types.KeyboardButton("/Update_leads"))

    write_in_log(message)
    data_base = select_db.all_users()

    url_widget = 'https://widgets.comf5.ru/crm/28844278/'

    if admin_filter.check(message):
        button_online = admin_button_markup_online
        button_offline = admin_button_markup_offline
    else:
        button_online = markup_online
        button_offline = markup_offline

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

                data = {"status": 0}
                requests.post(
                    f"{url_widget}{users.get(message.text)}/Respool/6032/setStatus?token={dotenv_values('.env').get('WIDGET_TOKEN')}",
                    data=data)

                write_db.add_data(
                    Users(telegram_id=message.from_user.id, crm_id=users.get(message.text), username=message.from_user.username,
                          first_name=message.from_user.first_name, last_name=message.from_user.last_name, email=message.text)
                )

                await bot.send_message(message.chat.id,
                                       "✅Аккаунт авторизован!✅\n"
                                       "Сейчас вы находитесь в статусе 🔴'OFFLINE'.\n"
                                       "Для получения новых лидов, нажмите <b>'Online'</b>.",
                                       parse_mode="HTML",
                                       reply_markup=button_online)
            elif data_base.get(str(message.from_user.id)) is not None:
                crm_user_id = data_base.get(str(message.from_user.id))
                registered_mail = [mail for mail, id in users.items() if id == crm_user_id][0]
                await bot.send_message(message.chat.id,
                                       f'<b>Вы уже Авторизованы под логином {registered_mail}!</b>',
                                       parse_mode="HTML")
        else:
            if data_base.get(str(message.from_user.id)) is None:
                await bot.send_message(message.chat.id,
                                       f'Пользователь {message.text} не существует в AMOcrm!🤔\n'
                                       f'Необходимо пройти Авторизацию!\nПожалуйста, укажите <b>ваш логин AMOcrm.</b>',
                                       parse_mode="HTML")
            if data_base.get(str(message.from_user.id)) is not None:
                crm_user_id = data_base.get(str(message.from_user.id))
                registered_mail = [mail for mail, id in users.items() if id == crm_user_id][0]
                await bot.send_message(message.chat.id,
                                       f'Пользователь {message.text} не существует в AMOcrm!🤔\n'
                                       f'<b>И вы уже Авторизованы под логином {registered_mail}!</b>',
                                       parse_mode="HTML")

    # Change status in crm system for registered users in bot.
    elif (message.text == '🟢Online' or message.text == 'Online') and data_base.get(str(message.from_user.id)) is not None:
        crm_user_id = data_base.get(str(message.from_user.id))
        data = {"status": 1}
        requests.post(
            f"{url_widget}{crm_user_id}/Respool/6032/setStatus?token={dotenv_values('.env').get('WIDGET_TOKEN')}",
            data=data)
        await bot.send_message(message.chat.id,
                               "🔥Поздравляю, вы <b>'Online'</b>!🔥\nТеперь вы можете получать новые лиды.",
                               parse_mode="HTML",
                               reply_markup=button_offline)

    elif (message.text == '🔴Offline' or message.text == 'Offline') and data_base.get(str(message.from_user.id)) is not None:
        crm_user_id = data_base.get(str(message.from_user.id))
        data = {"status": 0}
        requests.post(
            f"{url_widget}{crm_user_id}/Respool/6032/setStatus?token={dotenv_values('.env').get('WIDGET_TOKEN')}",
            data=data)
        await bot.send_message(message.chat.id,
                               "⛔️Внимание вы <b>'Offline'</b>!⛔️\nТеперь вы не можете получать новые лиды!",
                               parse_mode="HTML",
                               reply_markup=button_online)

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
