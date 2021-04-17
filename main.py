from telegram.ext import Updater, MessageHandler, Filters
from telegram.ext import CallbackContext, CommandHandler
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove
import datetime
import time
from dotenv import load_dotenv
import os
import sqlite3

load_dotenv()
TOKEN = os.getenv('TOKEN')


class DataBase:
    def __init__(self, id_tg, id_chat):
        self.db = sqlite3.connect('datetime.db')
        self.cur = self.db.cursor()
        self.id_tg = id_tg
        self.id_chat = id_chat

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

    def editing(self, date_time):
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
    update.message.reply_text("Я бот time-manager, если ты хочешь узнать какие у меня есть команды напиши '/help'")


def help_(update, context):
    update.message.reply_text("/now, сегодняшняя дата, время до секунды\n"
                              "/timer ? секунд/минут/часов\n"
                              "/dtimer, удаление установленого таймера\n"
                              "/ctimer, редактирование установленого таймера")


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
        if timestamp == 'с':
            new_job = context.job_queue.run_once(task, due, context=chat_id)
            context.chat_data['job'] = new_job
            update.message.reply_text(f'Отлично! Вернусь через {text_message[1]} {units_text}')
    except:
        update.message.reply_text('Опять что-то не так, я хочу спать вообще-то')


def timer_remind(second):
    time.sleep(second)
    return


def addition(update, context):
    try:
        text_message = update.message.text.split(', ')
        date_, msg = text_message.split(',')
        date = datetime.datetime.strptime(date_, '%Y-%m-%d %H:%M:%S')
        today = datetime.datetime.now()
        delta = today - date
        DataBase.addition(update.message.chat_id, date, msg)
        timer_remind(delta)
        task(context, reminded=msg)
    except Exception:
        print(Exception.__class__)


def editing(update, context):
    text_message = update.message.text.split(' ')
    text_message = text_message[1:]


#    DataBase.editing()


def viewing(update, context):
    text_message = update.message.text.split(' ')
    text_message = text_message[1:]


#    DataBase.viewing()


def deletion(update, context):
    text_message = update.message.text.split(' ')
    text_message = text_message[1:]


#    DataBase.deletion()


def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("add", addition))
    dp.add_handler(CommandHandler("delete", deletion))
    dp.add_handler(CommandHandler("edit", editing))
    dp.add_handler(CommandHandler("viewing", viewing))
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help_))
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
