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
    def __init__(self, id_tg):
        self.db = sqlite3.connect('datetime.sqlite')
        self.cur = self.db.cursor()
        self.id_tg = id_tg

    def addition(self, date_time):
        res = self.cur.execute("""INSERT INTO date_users(date) VALUES (?)""", date_time).fetchall()

    def deletion(self, date_time):
        try:
            res = self.cur.execute("""DELETE FROM date_users WHERE date = ?""", date_time).fetchall()
            self.db.close()
            return 'kk'
        except:
            return 'error'

    def editing(self, date_time):
        res = self.cur.execute("""UPDATE date_users SET duration = '162' WHERE id = ? AND WHERE date = ?""",
                               (self.id_tg, date_time)).fetchall()

    def viewing(self, date_time):
        res = self.cur.execute("""SELECT * FROM users_id WHERE id_tg = ?""", self.id_tg).fetchall()
        res = self.cur.execute("""SELECT * FROM date_users WHERE id = ?""", res).fetchall()
        res = self.cur.execute("""SELECT * FROM date_users WHERE date = ?""", date_time).fetchall()


def start(update, context):
    update.message.reply_text("Я бот time-manager, если ты хочешь узнать какие у меня есть команды напиши '/help'")


def h(update, context):
    update.message.reply_text("/now, сегодняшняя дата, время до секунды\n"
                              "/timer ? секунд/минут/часов\n"
                              "/dtimer, удаление установленого таймера\n"
                              "/ctimer, редактирование установленого таймера")


def now(update, context):
    update.message.reply_text(datetime.datetime.now().strftime(f'{time.ctime(time.time())}'))


def task(context):
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
        if text_message[2][0] == 'с':
            if 'job' in context.chat_data:
                old_job = context.chat_data['job']
                old_job.schedule_removal()
            new_job = context.job_queue.run_once(task, due, context=chat_id)
            context.chat_data['job'] = new_job
            update.message.reply_text(f'Вернусь через {due} секу')
        elif text_message[2][0] == 'м':
            due = due * 60
            if 'job' in context.chat_data:
                old_job = context.chat_data['job']
                old_job.schedule_removal()
            new_job = context.job_queue.run_once(task, due, context=chat_id)
            context.chat_data['job'] = new_job
            update.message.reply_text(f'Вернусь через {int(text_message[1])} мин')
        elif text_message[2][0] == 'ч':
            due = due * 60 * 60
            if 'job' in context.chat_data:
                old_job = context.chat_data['job']
                old_job.schedule_removal()
            new_job = context.job_queue.run_once(task, due, context=chat_id)
            context.chat_data['job'] = new_job
            update.message.reply_text(f'Вернусь через {int(text_message[1])} час')
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
            update.message.reply_text('Нет активного таймера')
            return
        chat_id = update.message.chat_id
        text_message = update.message.text.split(' ')
        due = int(text_message[1])
        if 'job' in context.chat_data:
            old_job = context.chat_data['job']
            old_job.schedule_removal()
        print(text_message[2][0] == 'с')
        if text_message[2][0] == 'с':
            new_job = context.job_queue.run_once(task, due, context=chat_id)
            context.chat_data['job'] = new_job
            update.message.reply_text(f'Отлично! Вернусь через {due} секу')
        if text_message[2][0] == 'м':
            new_job = context.job_queue.run_once(task, due, context=chat_id)
            context.chat_data['job'] = new_job
            update.message.reply_text(f'Отлично! Вернусь через {due * 60} секу')
        if text_message[2][0] == 'ч':
            new_job = context.job_queue.run_once(task, due, context=chat_id)
            context.chat_data['job'] = new_job
            update.message.reply_text(f'Отлично! Вернусь через {due * 60 * 60} секу')
    except:
        update.message.reply_text('Опять что-то не так, я хочу спать вообще-то')


def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("add", DataBase.addition))
    dp.add_handler(CommandHandler("delete", DataBase.editing))
    dp.add_handler(CommandHandler("edit", DataBase.deletion))
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", h))
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
2. прописать комманды
    1. #start, help
    2. #дата, время сейчас
    3. #создание таймера
    4. #удаление
    5. редактировние
3. настроить интуитивно понятную клавиатуру или сделать комманду помощь.
4. возможность пользователя добавлять, удалять, редактировать напоминания.
5. взаимодействия с бд.
5. возможность напоминания в иных мессенджерах
6. получение всего расписания за какой либо промежуток времени.
'''
