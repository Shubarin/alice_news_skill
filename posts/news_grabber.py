# coding=utf-8
import configparser
import datetime as dt
import json
import sqlite3
import os

from telethon.sync import TelegramClient
from telethon import connection

# для корректного переноса времени сообщений в json
from datetime import date, datetime

# классы для работы с каналами
from telethon.tl.functions.channels import GetParticipantsRequest
from telethon.tl.types import ChannelParticipantsSearch

# класс для работы с сообщениями
from telethon.tl.functions.messages import GetHistoryRequest

# Считываем учетные данные
config = configparser.ConfigParser()
config.read("config.ini")

# Присваиваем значения внутренним переменным
api_id = config['Telegram']['api_id']
api_hash = config['Telegram']['api_hash']
username = config['Telegram']['username']

client = TelegramClient(username, api_id, api_hash)

client.start()


async def dump_all_messages(channel):
    """Записывает json-файл с информацией о всех сообщениях канала/чата"""
    offset_msg = 0  # номер записи, с которой начинается считывание
    limit_msg = 100  # максимальное число записей, передаваемых за один раз

    all_messages = []  # список всех сообщений
    total_messages = 0
    total_count_limit = 100  # количество сообщений, которые нужно получить

    class DateTimeEncoder(json.JSONEncoder):
        '''Класс для сериализации записи дат в JSON'''

        def default(self, o):
            if isinstance(o, datetime):
                return o.isoformat()
            if isinstance(o, bytes):
                return list(o)
            return json.JSONEncoder.default(self, o)

    while True:
        history = await client(GetHistoryRequest(
            peer=channel,
            offset_id=offset_msg,
            offset_date=None, add_offset=0,
            limit=limit_msg, max_id=0, min_id=0,
            hash=0))
        if not history.messages:
            break
        messages = history.messages
        for message in messages:
            all_messages.append(message.to_dict())
        offset_msg = messages[len(messages) - 1].id
        total_messages = len(all_messages)
        if total_count_limit != 0 and total_messages >= total_count_limit:
            break

    db_name = 'db.sqlite'
    con = sqlite3.connect(db_name)
    cur = con.cursor()
    for line in all_messages:
        try:
            id = line['id']
            message = line['message']
            if not message:
                continue
            pub_date = line['date'].strftime("%Y-%m-%d %I:%M:%S")
            cur.execute("INSERT INTO news(id,message,pub_date) "
                        f"VALUES({id}, '{message}', '{pub_date}')")
        except sqlite3.IntegrityError:
            break
        except:
            continue
    con.commit()
    con.close()


async def main():
    url = "https://t.me/QryaProDucktion"
    channel = await client.get_entity(url)
    await dump_all_messages(channel)


with client:
    client.loop.run_until_complete(main())