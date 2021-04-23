from telegram.ext import Updater, MessageHandler, Filters
from telegram.ext import CallbackContext, CommandHandler
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove
from datetime import time
import datetime
import time
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

keyboard = [["/help", "/weather"],
            ["/world_time", "закрыть клавиатуру"]]
markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=False)
dice_keyboard = [["30 секунд", "1 минута"],
                 ["5 минут", "закрыть клавиатуру"]]
markup_dice = ReplyKeyboardMarkup(dice_keyboard, one_time_keyboard=False)


def start(update, context):
    update.message.reply_text(
        "Я бот time-manager, если ты хочешь узнать какие у меня есть команды напиши '/help'",
        reply_markup=markup)


def help_(update, context):
    update.message.reply_text("/now, сегодняшняя дата, время до секунды\n"
                              "/timer ? секунд/минут/часов\n"
                              "/dtimer, удаление установленого таймера\n"
                              "/edtimer, редактирование установленого таймера"
                              "/weather, погода\n"
                              "/world_time, мировое время\n"
                              )


def helper_function(update, context):
    if str(update.message.text).lower() == "закрыть клавиатуру":
        close_keyboard(update, context)


def close_keyboard(update, context):
    update.message.reply_text(
        "Ok",
        reply_markup=ReplyKeyboardRemove()
    )


class DataBase:
    def __init__(self, id_chat):
        self.db = sqlite3.connect("data/db/datetime.db")
        self.cur = self.db.cursor()
        self.id_chat = id_chat

    def vk_add(self, id_on_vk):
        self.cur.execute(
            """INSERT INTO user id_chat VALUES ?""", self.id_chat).fetchall()
        self.db.commit()
        self.db.close()

    def addition(self, date, reminding):
        user_id = self.cur.execute(
            """SELECT id_user_base FROM user WHERE id_chat = ?""", (self.id_chat,)).fetchone()[0]
        if not user_id:
            self.cur.execute(
                """INSERT INTO user id_chat VALUES ?""", (self.id_chat,))
        self.cur.execute(
            """INSERT INTO users_to_date(date, id_user_base) VALUES (?,?)""", (date, user_id))
        self.cur.execute(
            """INSERT INTO reminding(description, id_user_base) VALUES (?,?)""", (reminding, user_id))
        self.db.commit()
        self.db.close()

    def deletion(self, date_time=None, msg=None):
        if date_time is not None:
            id_on_base = self.cur.execute(
                """SELECT id_user_base FROM user WHERE id_chat = ?""", (self.id_chat,)).fetchone()[0]
            print(id_on_base)
            id_remind = self.cur.execute(
                """SELECT date_id FROM users_to_date WHERE id_user_base = ? AND date = ?""",
                (id_on_base, date_time)).fetchone()[0]
            print(id_remind)
            if id_remind is None:
                return 'Error'
            self.cur.execute(
                """DELETE FROM reminding WHERE id_chat = ?, """, id_remind)
            self.cur.execute(
                """DELETE FROM users_to_date WHERE id_chat = ?, """, id_remind)
            self.cur.execute(
                """DELETE FROM dates_id WHERE id_chat = ?, """, id_remind)
        elif msg is not None:
            id_on_base = self.cur.execute(
                """SELECT id_user_base FROM user WHERE id_chat = ?""", (self.id_chat,)).fetchone()[0]
            id_remind = self.cur.execute(
                """SELECT date_id FROM reminding WHERE id_user_base = ? AND date = ?""",
                (id_on_base, msg)).fetchone()[0]
            if id_remind is None:
                return 'Error'
            self.cur.execute(
                """DELETE FROM reminding WHERE id_chat = ?, """, id_remind)
            self.cur.execute(
                """DELETE FROM users_to_date WHERE id_chat = ?, """, id_remind)
            self.cur.execute(
                """DELETE FROM dates_id WHERE id_chat = ?, """, id_remind)
        self.db.commit()
        self.db.close()
        return 'kk'

    def editing(self, date_time, reminding):
        res = self.cur.execute(
            """UPDATE имя_таблицы SET название_колонки = новое_значение WHERE условие""",
            (self.id_chat, date_time)).fetchall()

    def viewing(self, from_date, until_date):
        user_id = self.cur.execute(
            """SELECT id_user_base FROM user WHERE id_tg = ?""", self.id_chat).fetchone()[0]
        res = self.cur.execute(
            """SELECT * FROM users_to_date WHERE id = ? AND""", user_id).fetchall()
        return res


def timer_remind(second):
    time.sleep(int(second))
    print("YOU")


def addition(update, context):
    try:
        date_, msg = update.message.text.split(', ')
        _, date_, time_ = date_.split()
        d, m, y = map(int, date_.split('.'))
        hour, minutes = map(int, time_.split(':'))
        new_date = datetime.datetime(year=2000 + y, month=m, day=d, hour=hour, minute=minutes)
        today = datetime.datetime.now()
        delta = today - new_date
        db_sess = DataBase(id_chat=update.message.chat_id)
        db_sess.addition(new_date, msg)
        print(delta.seconds)
        timer_remind(delta.seconds)
        task(context, reminded=msg)
        update.message.reply_text('Успешно')
    except Exception as e:
        print(e)


def editing(update, context):
    # /edit 14.04.2021 14:00 remind on remindx2 or /edit remind on date or /edit 14.04.2021 14:00
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


def viewing(update, context):  # /view 21.04.21-23.04.21
    try:
        _, dates_ = update.message.text.split()
        from_date, until_date = dates_.split('-')
        d, m, y = map(int, from_date.split('.'))
        from_date = datetime.datetime(year=2000 + y, month=m, day=d)
        d, m, y = map(int, until_date.split('.'))
        until_date = datetime.datetime(year=2000 + y, month=m, day=d)
        db_sess = DataBase(id_chat=update.message.chat_id)
        print(db_sess.viewing(from_date, until_date))
    except Exception:
        print(Exception.__class__)


def deletion(update, context):
    try:
        slow = {'kk': 'Сделано',
                'error': 'Ты что-то с датой напутал, хм...'}
        answer = ''
        db_sess = DataBase(id_chat=update.message.chat_id)
        if ':' in update.message.text:
            _, date_, time_ = update.message.text.split()
            d, m, y = map(int, date_.split('.'))
            hour, minutes = map(int, time_.split(':'))
            new_date = datetime.datetime(year=2000 + y, month=m, day=d, hour=hour, minute=minutes)
            print(new_date)
            answer = slow[db_sess.deletion(new_date)]
        elif ':' not in update.message.text:
            msg = update.message.text[1:]
            answer = slow[db_sess.deletion(msg=msg)]
        elif ', ' in update.message.text:
            text_message = update.message.text(', ')
            date_, msg = text_message
            _, date_, time_ = date_.split()
            d, m, y = map(int, date_.split('.'))
            hour, minutes = map(int, time_.split(':'))
            new_date = datetime.datetime(year=2000 + y, month=m, day=d, hour=hour, minute=minutes)
            answer = slow[db_sess.deletion(new_date, msg)]
        update.message.text(answer)
    except Exception as e:
        print(e)


def add_vk(update, context):
    try:
        text_message = update.message.text.split(', ')
    except Exception:
        print(Exception.__class__)


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


def unset_timer(update, context):
    if 'job' not in context.chat_data:
        update.message.reply_text('Нет активного таймера')
        return
    job = context.chat_data['job']
    job.schedule_removal()
    del context.chat_data['job']
    update.message.reply_text('Хорошо, вернулся сейчас!')


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
    dp.add_handler(CommandHandler("start", start))  # ...................Начало...................
    dp.add_handler(CommandHandler("help", help_))
    dp.add_handler(CommandHandler("close", close_keyboard))

    dp.add_handler(CommandHandler("add", addition))  # ...................Основные функции...................
    dp.add_handler(CommandHandler("delete", deletion))
    dp.add_handler(CommandHandler("edit", editing))
    dp.add_handler(CommandHandler("view", viewing))
    dp.add_handler(CommandHandler("add_vk", add_vk))

    dp.add_handler(CommandHandler("world_time", world_time_def))  # ...................доп. плюшки...................
    dp.add_handler(CommandHandler("weather", weather))
    dp.add_handler(CommandHandler("now", now))
    dp.add_handler(CommandHandler("timer", timer))
    dp.add_handler(CommandHandler("dtimer", unset_timer, pass_chat_data=True))
    dp.add_handler(CommandHandler("edtimer", change_timer))

    dp.add_handler(MessageHandler(Filters.text, helper_function))  # ...................Начало...................

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
