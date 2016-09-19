# -*- coding: utf-8 -*-
from telegram import *
from telegram.ext import *
from bottoken import TOKEN, creatorid
from os import path
import logging, time, math, pickle
#import json

TIME_FORMAT = "%d %b, %H:%M:%S"
logging.basicConfig(format = '%(levelname)-8s [%(asctime)s] %(message)s', level = logging.INFO,
	datefmt = TIME_FORMAT)

botid = int(TOKEN[:TOKEN.index(':')])

help_text = """Привет. Я бот, который считает карму в чате :)
Если ты хочешь узнать свою статистику, напиши /mystat или /st
Если тебе нужен топ пользователей, напиши /topstat или /top
Для перевода кармы используй /pay
-А для запроса о переводе кармы — /ask
Если вы хотите поблагодарить человека, используйте /thanks или /tx
-Если тебе надо подписаться на изменения своей кармы, напиши /carmasubscr
-Для отписки — /carmaunsubscr

Каждый день самым активным пользователям чата — призы!
За 1 место — +10 к карме
За 2 место — +5 к карме
За 3 место — +2 к карме
_____
Инфо о боте —> /about
Строки, начинающиеся с - обозначают ещё не реализованную возможность"""

about_text = """Я бот, который считает карму в чате :)
По всем вопросам, обращайся к моему создателю —> @evgfilim1
Если вы хотите помочь написанию бота, вам сюда —> @itcat_carma"""

features_text = """Фичи за карму:
Название - Цена - Как получить
Досрочный разбан - 50 - /feature 0
Отправка сообщения во время бана - 5 - /feature 1
Передать всем привет - 1 - /feature 2
Получить подарок на праздник - (-2) - /feature 3
Устроить раздачу - 100 - /feature 4
Уметь отнимать карму - 1000 - /feature 5"""

defaultAdminCarma = 2500
defaultUserCarma = -20
addViaThanks = 1
transferLimit = 256

filters = [Filters.audio,
	Filters.contact,
	Filters.command,
	Filters.document,
	Filters.location,
	Filters.photo,
	Filters.status_update,
	Filters.sticker,
	Filters.text,
	Filters.venue,
	Filters.video,
	Filters.voice]

carma = {}
msgcount = {}
unames = {}
#bank = {}
#subscribed = []

def error(bot, update, error):
	logging.warning('Update "{0}" caused error "{1}"'.format(update, error))
	bot.sendMessage(update.message.chat_id, text="Произошла ошибка при обработке этого сообщения", 
		reply_to_message=update.message.message_id)

def payment(chat_id, from_id, to_id, amount):
	global carma
	if from_id != 0:
		carma[chat_id][from_id] = carma[chat_id].get(from_id, defaultUserCarma) - amount
	carma[chat_id][to_id] = carma[chat_id].get(to_id, defaultUserCarma) + amount

def getuname(user):
	if bool(user.username):
		return user.username
	else:
		return user.first_name

def onStuff(bot, update):
	global msgcount, unames
	uid = update.message.from_user.id
	gid = update.message.chat_id
	if uid != gid:
		msgcount[gid][uid] = msgcount[gid].get(uid, 0) + 1
	if not uid in carma[gid]:
		carma[gid][uid] = defaultUserCarma
	unames.update({uid: getuname(update.message.from_user)})


def jobdaily(bot, job):
	global msgcount
	items = list(msgcount.items())
	for c in items:
		chat = c[1]
		cid = c[0]
		sorttop = sorted(chat.items(), key=lambda x: x[1], reverse=True)
		bonus = 10
		for u in range(3):
			try:
				usrid = sorttop[u][0]
			except IndexError:
				break
			carma[cid][usrid] = carma[cid].get(usrid, 0) + bonus
			bonus = bonus // 2

	for chats in msgcount:
		chats.clear()

def jobhourly(bot, job):
	with open('msg.pkl', 'wb') as f:
		pickle.dump(msgcount, f, pickle.HIGHEST_PROTOCOL)
	with open('carma.pkl', 'wb') as f:
		pickle.dump(carma, f, pickle.HIGHEST_PROTOCOL)
	logging.info("data saved.")

def start(bot, update, args):
	global carma, msgcount
	chat_id = update.message.chat_id
	if len(args) != 0 and update.message.from_user.id == creatorid:
		if args[0] == 'flush':
			jobhourly(None, None)
			bot.sendMessage(chat_id, text="Экстренная запись на диск выполнена")
		elif args[0] == 'spin':
			jobdaily(None, None)
			bot.sendMessage(chat_id, text="Экстренная раздача кармы по топу сообщений выполнена")
		elif args[0] == 'dbgvar':
			bot.sendMessage(update.message.chat_id, text="{}".format(eval(args[1])))
		return
	if chat_id == update.message.from_user.id:
		bot.sendMessage(chat_id, text="Готово, теперь вы можете получать уведомления.")
		return
	if chat_id in carma:
		if len(args) == 1 and args[0] == 'reinit' and update.message.from_user.id == creatorid:
			bot.sendMessage(chat_id, text="Реинициализация чата...")
		else:
			bot.sendMessage(chat_id, text="Этот чат уже инициализирован")
			return
	carma[chat_id] = {}
	msgcount[chat_id] = {}
	#bank[chat_id] = 0
	admins = bot.getChatAdministrators(chat_id)
	for admin in admins:
		carma[chat_id].update({admin.user.id: defaultAdminCarma})
		msgcount[chat_id].update({admin.user.id: 0})
		unames.update({admin.user.id: getuname(admin.user)})

	bot.sendMessage(chat_id, text="Чат инициализирован. /help")

def Help(bot, update):
	bot.sendMessage(update.message.chat_id, text=help_text)

def about(bot, update):
	bot.sendMessage(update.message.chat_id, text=about_text)

def mystat(bot, update):
	msg = update.message
	if bool(msg.reply_to_message):
		uu = msg.reply_to_message.from_user
		uid = uu.id
	else:
		uu = msg.from_user
		uid = uu.id
	text = """Статистика пользователя {u}:
Карма: {c}
Сообщений за день: {m}""".format(u=getuname(uu), c=carma[msg.chat_id].get(uid, defaultUserCarma), 
	m=msgcount[msg.chat_id].get(uid, 0))

	bot.sendMessage(msg.chat_id, text=text)

def topstat(bot, update):
	chat_id = update.message.chat_id
	chat = msgcount[chat_id]
	sorttop = sorted(chat.items(), key=lambda x: x[1], reverse=True)
	msg = "Статистика пользователей: \n"
	for i in range(10):
		try:
			un = unames.get(sorttop[i][0], "Unknown user {}".format(sorttop[i][0]))
		except IndexError:
			break
		msg += "{}: {} сообщений, {} кармы\n".format(un, sorttop[i][1], carma[chat_id].get(sorttop[i][0], defaultUserCarma))
	bot.sendMessage(chat_id, text=msg)

def pay(bot, update, args):
	vals = list(unames.values())
	fromid = update.message.from_user.id
	chat_id = update.message.chat_id
	fail = False
	try:
		arg = int(args[0])
	except:
		fail = True

	if not bool(update.message.reply_to_message):
		fail = True

	if fail:
		bot.sendMessage(chat_id, text="Использование: (в ответ на сообщение получателя) /pay <сумма>")
		return
	else:
		toid = update.message.reply_to_message.from_user.id
		if arg < 0:
			arg = -arg
		arg = int(arg % transferLimit)
	
	if toid == botid:
		toid = creatorid

	payment(chat_id, fromid, toid, arg)
	bot.sendMessage(chat_id, text="{} кармы переведено.".format(arg))
		
def thnx(bot, update):
	chat_id = update.message.chat_id
	if not bool(update.message.reply_to_message):
		bot.sendMessage(chat_id, text="Использование: (в ответ на сообщение получателя) /thanks")
		return
	u = update.message.reply_to_message.from_user
	if u.id == update.message.from_user.id:
		bot.sendMessage(chat_id, text="Жулик, не воруй!")
		return
	elif u.id == botid:
		u.id = creatorid
	payment(chat_id, 0, u.id, 1)
	bot.sendMessage(chat_id, text="Добавлено +1 к карме {}".format(getuname(u)))

def statusupdate(bot, update):
	if not bool(update.message.new_chat_member):
		return
	if update.message.new_chat_member.id == botid:
		start(bot, update)

def myid(bot, update):
	if bool(update.message.reply_to_message):
		uid = update.message.reply_to_message.from_user.id
	else:
		uid = update.message.from_user.id
	bot.sendMessage(update.message.chat_id, text="UID: {0}, GID: {1}".format(uid, update.message.chat_id))

# def pidr(bot, update):
# 	bot.sendMessage(update.message.chat_id, text="Спец по пидорам --> @mrsteyk")

updater = Updater(TOKEN)
del TOKEN

jobs = updater.job_queue

jobs.put(Job(jobhourly, 3600.0))
jobs.put(Job(jobdaily, 86400.0))

dp = updater.dispatcher

dp.add_handler(CommandHandler('start', start, pass_args=True))
dp.add_handler(CommandHandler('help', Help))
dp.add_handler(CommandHandler('about', about))
dp.add_handler(CommandHandler('myid', myid))
dp.add_handler(CommandHandler('mystat', mystat))
dp.add_handler(CommandHandler('st', mystat))
dp.add_handler(CommandHandler('topstat', topstat))
dp.add_handler(CommandHandler('top', topstat))
dp.add_handler(CommandHandler('pay', pay, pass_args=True))
dp.add_handler(CommandHandler('thanks', thnx))
dp.add_handler(CommandHandler('tx', thnx))
#dp.add_handler(CommandHandler('pidorspec', pidr))
dp.add_handler(MessageHandler([Filters.status_update], statusupdate))
dp.add_handler(MessageHandler([], onStuff))

dp.add_error_handler(error)

if path.exists('msg.pkl'):
	with open('msg.pkl', 'rb') as f:
		msgcount = pickle.load(f)
	with open('carma.pkl', 'rb') as f:
		carma = pickle.load(f)
	logging.info("data loaded.")

updater.start_polling()
updater.idle()

jobhourly(None, None)