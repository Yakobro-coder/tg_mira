import requests
import json
import logging
from datetime import datetime, timedelta
import pytz
import time
from dotenv import dotenv_values

from models.users_model import Admin
from db_foo import select_db

tmz = pytz.timezone(dotenv_values('.env').get('TIMEZONE'))

logging.basicConfig(filename='logs/schedule_log',
                    format=f"[{datetime.now(tmz)}] %(levelname)s: \"%(message)s\"",
                    level=logging.INFO)

time_refresh = timedelta(hours=8, minutes=0, seconds=0)
time_stop = time_refresh + timedelta(minutes=1)

logging.info("### START SCHEDULE!!! ###")
while True:
    dt = datetime.now(tmz)
    now_time = timedelta(hours=dt.hour, minutes=dt.minute, seconds=dt.second)

    if time_refresh < now_time < time_stop:
        token = select_db.get_token()
        headers = {"Authorization": token}
        params = {
            "filter[responsible_user_id]": 8538668,  # admin8:8538668    admin:7539577
            "filter[statuses][0][pipeline_id]": 3414178,  # REGISTERED LEADS
            "filter[statuses][0][status_id]": 34017646,  # NEW LEAD
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
        elif send_leads_in_new_lead.status_code == 200:
            word = ""
            if len(leads_id) == 1:
                word = "лид"
            elif 1 < len(leads_id) < 5:
                word = "лидa"
            elif 4 < len(leads_id) or len(leads_id) == 0:
                word = "лидов"

            for chat_id in Admin.ADMIN.value:
                data = {
                    "chat_id": chat_id,
                    "text": f"<b>Автоматическое распределение выполнено!♻\nРаспределено: {len(leads_id)} {word}!</b>",
                    "parse_mode": "html"
                }
                res = requests.post(f"https://api.telegram.org/bot{dotenv_values('.env').get('TOKEN')}/sendMessage",
                                    data=data)

        time.sleep(600)
    time.sleep(1)
