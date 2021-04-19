from telegram.ext import Updater, MessageHandler, Filters
from telegram.ext import CallbackContext, CommandHandler
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove
import datetime
import time
from datetime import time
from dotenv import load_dotenv
import os
import sqlite3
import vk_api
import random
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
import pyowm
from bs4 import BeautifulSoup
import requests

load_dotenv()
TOKEN = os.getenv("TOKEN")
TOKEN_VK = os.getenv("TOKEN_VK")
id_group_vk = os.getenv("id_group_vk")
owm = pyowm.OWM("77747d4628e230296e6b495f66c3b817")

keyboard = [["help", "weather"],
            ["world_time", "закрыть клавиатуру"]]
markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=False)
dice_keyboard = [["30 секунд", "1 минута"],
                 ["5 минут", "закрыть клавиатуру"]]
markup_dice = ReplyKeyboardMarkup(dice_keyboard, one_time_keyboard=False)


class DataBase:
    def __init__(self, id_tg, id_chat):
        self.db = sqlite3.connect("datetime.db")
        self.cur = self.db.cursor()
        self.id_tg = id_tg
        self.id_chat = id_chat

    def vk_add(self, id_on_vk):
        self.cur.execute(
            """INSERT INTO user(id_tg, id_chat) VALUES (?,?)""", (self.id_tg, self.id_chat)).fetchall()
        self.db.commit()
        self.db.close()

    def addition(self, date, reminding):
        self.cur.execute(
            """INSERT INTO user(id_tg, id_chat) VALUES (?,?)""", (self.id_tg, self.id_chat)).fetchall()
        id_base = self.cur.execute(
            """SELECT * FROM user WHERE id_tg = ?""", self.id_tg).fetchall()
        self.cur.execute(
            """INSERT INTO users_to_date(date, user) VALUES (?,?)""", (date, 1)).fetchall()
        self.cur.execute(
            """INSERT INTO reminding(description, target) VALUES (?,?)""", (reminding, 1)).fetchall()
        self.db.commit()
        self.db.close()

    def deletion(self, date_time):
        try:
            res = self.cur.execute(
                """DELETE FROM date_users WHERE date = ?""", date_time).fetchall()
            self.db.close()
            return 'kk'
        except:
            return 'error'

    def editing(self, date_time, reminding):
        res = self.cur.execute(
            """UPDATE имя_таблицы SET название_колонки = новое_значение WHERE условие""",
            (self.id_tg, date_time)).fetchall()

    def viewing(self, date_time):
        id_base = self.cur.execute(
            """SELECT * FROM user WHERE id_tg = ?""", self.id_tg).fetchall()
        res = self.cur.execute(
            """SELECT * FROM users_to_date WHERE id = ?""", self.id_tg).fetchall()
        print(res)
        return res


def start(update, context):
    update.message.reply_text(
        "Я бот time-manager, если ты хочешь узнать какие у меня есть команды напиши '/help'",
        reply_markup=dice_keyboard)


def help_(update, context):
    update.message.reply_text("/now, сегодняшняя дата, время до секунды\n"
                              "/timer ? секунд/минут/часов\n"
                              "/dtimer, удаление установленого таймера\n"
                              "/ctimer, редактирование установленого таймера"
                              "/weather, погода\n"
                              "/world_time, мировое время\n"
                              )


def now(update, context):
    update.message.reply_text(datetime.datetime.now().strftime(f'{time.ctime(time.time())}'))


def task(context, reminded=None):
    if reminded is not None:
        job = context.job
        context.bot.send_message(job.context, text=reminded)
    else:
        job = context.job
        context.bot.send_message(job.context, text='Вернулся!')


def timer(update, context):
    text_message = update.message.text.split(' ')
    try:
        due = int(text_message[1])
        chat_id = update.message.chat_id
        if due <= 0:
            update.message.reply_text('Извините, мы не умеем возвращаться в прошлое...')
            return
        timestamp = text_message[2][0]
        messages = {"с": (1, "секунд"),
                    "м": (60, "минут"),
                    "ч": (60 * 60, "часов")}
        due = due * messages[timestamp][0]
        units_text = messages[timestamp][1]
        if timestamp == "с":
            if "job" in context.chat_data:
                old_job = context.chat_data['job']
                old_job.schedule_removal()
            new_job = context.job_queue.run_once(task, due, context=chat_id)
            context.chat_data['job'] = new_job
            update.message.reply_text(f'Вернусь через {text_message[1]} {units_text}')
    except Exception:
        update.message.reply_text('Ты просишь от меня невозможного :с')


def unset_timer(update, context):
    if 'job' not in context.chat_data:
        update.message.reply_text('Нет активного таймера')
        return
    job = context.chat_data['job']
    job.schedule_removal()
    del context.chat_data['job']
    update.message.reply_text('Хорошо, вернулся сейчас!')


def change_timer(update, context):
    try:
        if 'job' not in context.chat_data:
            update.message.reply_text("Нет активного таймера")
            return
        chat_id = update.message.chat_id
        text_message = update.message.text.split(' ')
        due = int(text_message[1])
        timestamp = text_message[2][0]
        messages = {"с": (1, "секунд"),
                    "м": (60, "минут"),
                    "ч": (60 * 60, "часов")}
        due = due * messages[timestamp][0]
        units_text = messages[timestamp][1]
        if 'job' in context.chat_data:
            old_job = context.chat_data['job']
            old_job.schedule_removal()
        if timestamp == messages:
            new_job = context.job_queue.run_once(task, due, context=chat_id)
            context.chat_data['job'] = new_job
            update.message.reply_text(f'Отлично! Вернусь через {text_message[1]} {units_text}')
        elif timestamp == messages:
            pass

    except:
        update.message.reply_text('Опять что-то не так, я хочу спать вообще-то')


def timer_remind(second):
    time.sleep(second)
    return


def addition(update, context):
    try:
        text_message = update.message.text.split(', ')
        date_, msg = text_message.split(',')
        date_, time_ = date_.split()
        d, m, y = map(int, date_.split('.'))
        hour, minutes = map(int, time_.split(':'))
        new_date = datetime.datetime(year=2000 + y, month=m, day=d, hour=hour, minute=minutes)
        today = datetime.datetime.now()
        delta = today - new_date
        DataBase.addition(update.message.chat_id, new_date, msg)
        timer_remind(delta)
        task(context, reminded=msg)
        print(new_date, msg)
    except Exception:
        print(Exception.__class__)


def editing(update, context):
    try:
        text_message = update.message.text.split(', ')
        date_, msg = text_message.split(',')
        date_, time_ = date_.split()
        d, m, y = map(int, date_.split('.'))
        hour, minutes = map(int, time_.split(':'))
        new_date = datetime.datetime(year=2000 + y, month=m, day=d, hour=hour, minute=minutes)
        DataBase.editing(update.message.chat_id, new_date, msg)
        task(context, reminded=msg)
    except Exception:
        print(Exception.__class__)


def viewing(update, context):
    try:
        text_message = update.message.text.split(', ')
        date_, msg = text_message.split(',')
        date_, time_ = date_.split()
        d, m, y = map(int, date_.split('.'))
        hour, minutes = map(int, time_.split(':'))
        new_date = datetime.datetime(year=2000 + y, month=m, day=d, hour=hour, minute=minutes)
        today = datetime.datetime.now()
        delta = today - new_date
        DataBase.viewing(update.message.chat_id, new_date, msg)
        timer_remind(delta)
        task(context, reminded=msg)
    except Exception:
        print(Exception.__class__)


def deletion(update, context):
    try:
        text_message = update.message.text.split(', ')
        date_, msg = text_message.split(',')
        date_, time_ = date_.split()
        d, m, y = map(int, date_.split('.'))
        hour, minutes = map(int, time_.split(':'))
        new_date = datetime.datetime(year=2000 + y, month=m, day=d, hour=hour, minute=minutes)
        today = datetime.datetime.now()
        delta = today - new_date
        DataBase.deletion(update.message.chat_id, new_date, msg)
        timer_remind(delta)
        task(context, reminded=msg)
    except Exception:
        print(Exception.__class__)


def add_vk(update, context):
    try:
        text_message = update.message.text.split(', ')
        DataBase.vk_add(id_on_vk=text_message[1])
    except Exception:
        print(Exception.__class__)


def weather(update, context):
    try:
        text_message = update.message.text.split(' ')
        place = (text_message[1])
        mgr = owm.weather_manager()
        observation = mgr.weather_at_place(place)
        w = observation.weather
        temp = w.temperature("celsius")["temp"]
        forecast = f"В городе {place} и {w.detailed_status}, а температура {temp}°C"
        update.message.reply_text(forecast)
    except:
        update.message.reply_text("Какой странный город, попробуй еще раз")


def world_time_def(update, context):
    page = requests.get('https://www.google.com/search?q=Greenwich+Mean+Time&client=firefox-b-d&sxsrf=ALeKk03HNraW'
                        'LezxwWl3A0QJCXtwM6XG5g%3A1618849508829&ei=5K59YNqJMuXirgTuwZrwBQ&oq=Greenwich+Mean+Time&gs'
                        '_lcp=Cgdnd3Mtd2l6EAMyBAgAEEMyBQgAEMsBMgUIABDLATIECAAQQzIFCAAQyQMyAggAMgIIADICCAAyAggAMgIIA'
                        'FCkLlikLmCPNWgAcAJ4AIABVIgBmgGSAQEymAEAoAECoAEBqgEHZ3dzLXdpesABAQ&sclient=gws-wiz&ved=0ahU'
                        'KEwjai6yv3IrwAhVlsYsKHe6gBl4Q4dUDCA0&uact=5')
    soup = BeautifulSoup(page.text, "html.parser")
    parsed_time = soup.find_all('div', {'class': 'BNeawe iBp4i AP7Wnd'})[1].find_all(text=True, recursive=True)
    world_time = f"По гринвичу время {parsed_time[0]}"
    update.message.reply_text(world_time)


def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("add", addition))
    dp.add_handler(CommandHandler("delete", deletion))
    dp.add_handler(CommandHandler("edit", editing))
    dp.add_handler(CommandHandler("viewing", viewing))
    dp.add_handler(CommandHandler("add_vk", add_vk))
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help_))
    dp.add_handler(CommandHandler("world_time", world_time_def))
    dp.add_handler(CommandHandler("weather", weather))
    dp.add_handler(CommandHandler("now", now))
    dp.add_handler(CommandHandler("timer", timer))
    dp.add_handler(CommandHandler("dtimer", unset_timer))
    dp.add_handler(CommandHandler("ctimer", change_timer))
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
'''Задачи:
Для этого:
4. возможность пользователя добавлять, удалять, редактировать напоминания.
5. взаимодействия с бд.
5. возможность напоминания в иных мессенджерах
6. получение всего расписания за какой либо промежуток времени.
'''
