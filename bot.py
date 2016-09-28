# -*- coding: utf-8 -*-
from telegram import *
from telegram.ext import *
from botlibs.token import TOKEN
from botlibs.token import creatorid
from os import path
import logging, time, math, pickle

ddr = './botdata/'
dbgcid = -1001081124233

TIME_FORMAT = "%d %b, %H:%M:%S"
logging.basicConfig(format = '%(levelname)-8s [%(asctime)s] %(message)s', level = logging.INFO,
	datefmt = TIME_FORMAT)

botid = int(TOKEN[:TOKEN.index(':')])
#botuname = None

coinEmoji = '🐱'

help_text = """Привет. Я бот, который считает catcoin'ы (обозначаются как {e}) в чате :)
/mystat или /st — узнать статистику пользователя
/topstat или /top — топ пользователей по {e}
/msgtopstat или /mtop — топ пользователей по сообщениям
/pay — перевести {e}
/ask — попросить {e}
/thanks, /tx или "++" — +1 {e} для другого человека
/sub или /subscr — подписаться на изменения {e} (сообщения приходят в ЛС)
Для отписки — /unsub или /unsubscr

Каждый день самым активным пользователям чата — призы!
За 1 место — +10 {e}
За 2 место — +5 {e}
За 3 место — +2 {e}
_____
Ограничение всех трансферов: [0..1023]
Инфо о боте —> /about
Команды администрирования —> /admin
Вскоре будут доступны некоторые плюшки с тратой catcoin'ов, а пока, зарабатывайте их!""".format(e=coinEmoji)

hid_text = """Команды, не относящиеся непосредственно к боту:
/uid — узнать UID и GID
/whois — узнать, кто владелец определённого ID
Я могу тебе сказать, который сейчас час! :)
"""

about_text = """Я бот, который считает {e} в чате :)
По всем вопросам, обращайся к моему создателю —> @evgfilim1
Если вы хотите помочь написанию бота, вам сюда —> @itcat_carma""".format(e=coinEmoji)

features_text = """Фичи за {e}:
Название - Цена - Как получить
Отправка сообщения во время бана - 5 - /feature 1
Передать всем привет - 1 - /feature 2
Получить подарок на праздник - (-5) - /feature 3
Устроить раздачу - 50 - /feature 4
Испытать удачу - 10 - /feature 777
""".format(e=coinEmoji)

defaultUserCarma = 0
addViaThanks = 1
transferLimit = 1024

carma = {}
msgcount = {}
unames = {}
chatadmins = {}
subscribed = []
targets = {}

def error(bot, update, error):
	logging.warning('Update "{0}" caused error "{1}"'.format(update, error))
	bot.sendMessage(update.message.chat_id, text="Произошла ошибка при обработке этого сообщения", 
		reply_to_message_id=update.message.message_id)
		
def migrate_tov2(bot, update):
	t = """Миграция данных пользователей завершена.
----------
Бот обновлён!
Что нового в версии 2?
1) Включен тихий режим
2) Теперь можно писать боту в ЛС
3) Убрана фича by @Racc_oon (/pidor)
4) Карма переименована в Catcoin ({e})
5) Выпилены длинные команды
6) Теперь админы могут закрывать сбор кармы
7) Уведомление о получении ежедневного бонуса
""".format(e=coinEmoji)
	
	migrated = []
	for cid in carma:
		for usr in carma[cid]:
			migrated.append(usr)
			if carma[cid][usr] < -19:
				carma[cid][usr] = 0
			else:
				carma[cid][usr] = carma[cid][usr] + 20
	
	logging.info(migrated)
	jobhourly(None, None)
	bot.sendMessage(update.message.chat_id, text=t)

def payment(chat_id, from_id, to_id, amount, check=True):
	global carma
	fromcarma = carma[chat_id].get(from_id, defaultUserCarma)
	if check and amount > fromcarma:
		return False
	if from_id != 0:
		carma[chat_id][from_id] = fromcarma - amount
	if to_id != 0:
		carma[chat_id][to_id] = carma[chat_id].get(to_id, defaultUserCarma) + amount

	return True

def sendnotif(bot, from_id, to_id, amount):
	if from_id != 0 and from_id in subscribed:
		capt = ''
		if to_id != 0:
			capt = 'для пользователя {}'.format(unames.get(to_id, 'Unknown user {}'.format(to_id)))
		bot.sendMessage(from_id, text="У вас было отнято {0} {e} {1}".format(amount, capt, e=coinEmoji))
		del capt

	if to_id != 0 and to_id in subscribed:
		capt = ''
		if from_id != 0:
			capt = 'пользователем {}'.format(unames.get(from_id, 'Unknown user {}'.format(from_id)))
		bot.sendMessage(to_id, text="Вам было добавлено {0} {e} {1}".format(amount, capt, e=coinEmoji))

def getuname(user):
	if bool(user.username):
		return user.username
	else:
		return user.first_name
		
def inprivate(chat_id, from_id):
	return (chat_id == from_id)

def onStuff(bot, update):
	global msgcount, unames
	uid = update.message.from_user.id
	gid = update.message.chat_id
	if not inprivate(gid, uid):
		msgcount[gid][uid] = msgcount[gid].get(uid, 0) + 1
	if not uid in carma[gid]:
		carma[gid][uid] = defaultUserCarma
	unames.update({uid: getuname(update.message.from_user)})


def jobdaily(bot, job):
	global msgcount
	for cid in msgcount:
		chat = msgcount[cid]
		sorttop = sorted(chat.items(), key=lambda x: x[1], reverse=True)
		bonus = 10
		for u in range(3):
			try:
				usrid = sorttop[u][0]
			except IndexError:
				break
			carma[cid][usrid] = carma[cid].get(usrid, 0) + bonus
			sendnotif(bot, 0, usrid, bonus)
			bonus = bonus // 2

	for chat in msgcount:
		msgcount[chat].clear()
		
	logging.info("jobdaily done")

def jobhourly(bot, job):
	with open(ddr + 'msg.pkl', 'wb') as f:
		pickle.dump(msgcount, f, pickle.HIGHEST_PROTOCOL)
	with open(ddr + 'carma.pkl', 'wb') as f:
		pickle.dump(carma, f, pickle.HIGHEST_PROTOCOL)
	with open(ddr + 'unames.pkl', 'wb') as f:
		pickle.dump(unames, f, pickle.HIGHEST_PROTOCOL)
	with open(ddr + 'subs.pkl', 'wb') as f:
		pickle.dump(subscribed, f, pickle.HIGHEST_PROTOCOL)
	with open(ddr + 'admins.pkl', 'wb') as f:
		pickle.dump(chatadmins, f, pickle.HIGHEST_PROTOCOL)
	with open(ddr + 'targets.pkl', 'wb') as f:
		pickle.dump(targets, f, pickle.HIGHEST_PROTOCOL)
	logging.info("data saved.")

def start(bot, update, args):
	text = update.message.text.split()[0].split('@')
	if not ((len(text) == 2 and text[1] == botuname) or (len(text) == 1)):
		return
	
	try:
		target = int(args[0])
	except:
		target = None
	
	global carma, msgcount, chatadmins, unames
	chat_id = update.message.chat_id
	from_id = update.message.from_user.id
	
	if inprivate(chat_id, from_id):
		if target:
			ct = bot.getChat(target)
			if ct.type == 'private':
				bot.sendMessage(chat_id, text="ЛС? Я не умею считать Catcoin'ы в ЛС.")
				return
			targets.update({from_id: target})
			bot.sendMessage(chat_id, text="'{}' установлен как чат по умолчанию".format(ct.title))
			return
		else:
			bot.sendMessage(chat_id, text="""Готово, теперь вы можете получать уведомления.
Если вы хотите установить чат по умолчанию в ЛС (чтобы я реагировал на команды, как в чате), напишите в том чате /start getlink""")
			return

	if chat_id in carma:
		if len(args) > 0 and args[0] == 'clear' and update.message.from_user.id == creatorid:
			bot.sendMessage(chat_id, text="Реинициализация чата...", reply_to_message_id=update.message.message_id)
		elif len(args) > 0 and args[0] == 'getlink':
			bot.sendMessage(chat_id,
				text="[Установить этот чат в качестве чата по умолчанию в ЛС]({})".format(baselink.format(chat_id)),
				parse_mode="Markdown", disable_web_page_preview=True, reply_to_message_id=update.message.message_id)
			return
		else:
			bot.sendMessage(chat_id, text="Этот чат уже инициализирован", reply_to_message_id=update.message.message_id)
			return
	carma[chat_id] = {}
	msgcount[chat_id] = {}
	chatadmins[chat_id] = []
	admins = bot.getChatAdministrators(chat_id)
	for admin in admins:
		unames.update({admin.user.id: getuname(admin.user)})
		chatadmins[chat_id].append(admin.user.id)

	bot.sendMessage(chat_id, text="Чат инициализирован. /help")

def Help(bot, update):
	text = update.message.text.split()[0].split('@')
	if not ((len(text) == 2 and text[1] == botuname) or (len(text) == 1)):
		return
	
	try:
		bot.sendMessage(update.message.from_user.id, text=help_text)
	except:
		bot.sendMessage(update.message.chat_id, text="Невозможно отправить сообщение. Напиши в ЛС мне",
			reply_to_message_id=update.message.message_id)

def about(bot, update):
	bot.sendMessage(update.message.chat_id, text=about_text)

def hid(bot, update):
	try:
		bot.sendMessage(update.message.from_user.id, text=hid_text)
	except:
		bot.sendMessage(update.message.chat_id, text="Невозможно отправить сообщение. Напиши в ЛС мне",
			reply_to_message_id=update.message.message_id)

def button(bot, update):
	query = update.callback_query
	data = query.data.split(':')
	chat_id = query.message.chat_id
	msg_id = query.message.message_id
	inlmsgid = query.id
	qfrom = query.from_user.id

	if data[0] == 'asked':
		if data[2] == 'stop':
			if int(data[1]) == qfrom:
				bot.editMessageText(chat_id=chat_id, message_id=msg_id, reply_markup=InlineKeyboardMarkup([]),
					text="Сбор {e} остановлен владельцем.".format(e=coinEmoji))
			elif qfrom in chatadmins[chat_id]:
				bot.editMessageText(chat_id=chat_id, message_id=msg_id, reply_markup=InlineKeyboardMarkup([]),
					text="Сбор {e} остановлен Админом.".format(e=coinEmoji))
			else:
				bot.answerCallbackQuery(callback_query_id=inlmsgid,
					text="Вы не владелец этого сбора {e}".format(e=coinEmoji))
		else:
			if payment(chat_id, qfrom, int(data[1]), int(data[2]), True):
				bot.answerCallbackQuery(callback_query_id=inlmsgid,
					text="Успешно переведено {} {e}".format(data[2], e=coinEmoji))
				sendnotif(bot, qfrom, int(data[1]), int(data[2]))
			else:
				bot.answerCallbackQuery(callback_query_id=inlmsgid, text="Недостаточно {e}".format(e=coinEmoji))
	else:
		return

def adminpanel(bot, update, args):
	global carma, msgcount, unames, chatadmins, subscribed
	chat_id = update.message.chat_id
	from_id = update.message.from_user.id
	if from_id not in chatadmins[chat_id] and from_id != creatorid:
		bot.sendMessage(chat_id, text="Недостаточно прав", reply_to_message_id=update.message.message_id)
		return

	if len(args) == 0:
		bot.sendMessage(chat_id, text="""Available commands:
flush\nspin\nreinit\ngivecarma\nsetcarma\ntakecarma""", reply_to_message_id=update.message.message_id)

	else:
		cmd = args[0]
		args.pop(0)
		if cmd == 'flush':
			jobhourly(None, None)
			bot.sendMessage(chat_id, text="jobhourly done", reply_to_message_id=update.message.message_id)
			return
		elif cmd == 'spin':
			jobdaily(None, None)
			bot.sendMessage(chat_id, text="jobdaily done",  reply_to_message_id=update.message.message_id)
			return
		elif cmd == 'dbgvar' and from_id == creatorid:
			bot.sendMessage(chat_id, text='{}'.format(eval(' '.join(args))))
			return
		elif cmd == 'shell' and from_id == creatorid:
			eval(' '.join(args))
			return
		elif cmd == 'reinit':
			if args[0] == 'all':
				start(bot, update, ['clear'])
			elif args[0] == 'carma':
				carma[chat_id] = {}
			elif args[0] == 'msgcount':
				msgcount[chat_id] = {}
			elif args[0] == 'unames':
				unames = {}
			elif args[0] == 'chatadmins':
				chatadmins[chat_id] = []
				admins = bot.getChatAdministrators(chat_id)
				for admin in admins:
					chatadmins[chat_id].append(admin.user.id)
			elif args[0] == 'subscribed':
				subscribed = []
			else:
				bot.sendMessage(chat_id, text="Usage: /admin reinit [all|carma|msgcount|unames|chatadmins|subscribed]",
					reply_to_message_id=update.message.message_id)
			bot.sendMessage(chat_id, text="{} done".format(cmd + args[0]), reply_to_message_id=update.message.message_id)
			return
		elif cmd == 'givecarma':
			try:
				toid = int(args[0])
				amount = int(args[1])
			except:
				bot.sendMessage(chat_id, text="Usage: /admin givecarma <to_id> <amount>")
				return
			fromid = 0
			bot.sendMessage(chat_id, text="{} done".format(cmd), reply_to_message_id=update.message.message_id)
		elif cmd == 'setcarma':
			try:
				toid = int(args[0])
				amount = int(args[1])
			except:
				bot.sendMessage(chat_id, text="Usage: /admin setcarma <to_id> <amount>")
				return
			carma[chat_id][toid] = amount
			bot.sendMessage(chat_id, text="{} done".format(cmd), reply_to_message_id=update.message.message_id)
			return
		elif cmd == 'takecarma':
			try:
				fromid = int(args[0])
				amount = int(args[1])
			except:
				bot.sendMessage(chat_id, text="Usage: /admin takecarma <to_id> <amount>")
				return
			toid = 0
			bot.sendMessage(chat_id, text="{} done".format(cmd), reply_to_message_id=update.message.message_id)

		payment(chat_id, fromid, toid, amount)
		sendnotif(bot, fromid, toid, amount)

def mystat(bot, update):
	msg = update.message
	chat_id = msg.chat_id
	if bool(msg.reply_to_message):
		uu = msg.reply_to_message.from_user
		uid = uu.id
	else:
		uu = msg.from_user
		uid = uu.id
		
	if inprivate(chat_id, msg.from_user.id):
		chat_id = targets.get(chat_id, 0)
		if chat_id == 0:
			bot.sendMessage(msg.from_user.id, text="Вы не установили связь с чатом. /start для подробностей")
			return
	
	text = """Статистика пользователя {u}:
Catcoin'ы: {c}
Сообщений за день: {m}""".format(u=getuname(uu), c=carma[chat_id].get(uid, defaultUserCarma), 
	m=msgcount[chat_id].get(uid, 0))

	try:
		bot.sendMessage(update.message.from_user.id, text=text)
	except:
		bot.sendMessage(update.message.chat_id, text="Невозможно отправить сообщение. Напиши в ЛС мне",
			reply_to_message_id=update.message.message_id)

def topstat(bot, update):
	chat_id = update.message.chat_id
	from_id = update.message.from_user.id
	if inprivate(chat_id, from_id):
		chat_id = targets.get(chat_id, 0)
		if chat_id == 0:
			bot.sendMessage(from_id, text="Вы не установили связь с чатом. /start для подробностей")
			return
	
	chat = carma[chat_id]
	sorttop = sorted(chat.items(), key=lambda x: x[1], reverse=True)
	msg = "Статистика пользователей: \n"
	for i in range(10):
		try:
			un = unames.get(sorttop[i][0], "Unknown user {}".format(sorttop[i][0]))
		except IndexError:
			break
		msg += "{}: {} сообщений, {} {e}\n".format(un, msgcount[chat_id].get(sorttop[i][0], 0), sorttop[i][1], e=coinEmoji)

	try:
		bot.sendMessage(update.message.from_user.id, text=msg)
	except:
		bot.sendMessage(update.message.chat_id, text="Невозможно отправить сообщение. Напиши в ЛС мне",
			reply_to_message_id=update.message.message_id)

def mtopstat(bot, update):
	chat_id = update.message.chat_id
	from_id = update.message.from_user.id
	if inprivate(chat_id, from_id):
		chat_id = targets.get(chat_id, 0)
		if chat_id == 0:
			bot.sendMessage(from_id, text="Вы не установили связь с чатом. /start для подробностей")
			return

	chat = msgcount[chat_id]
	sorttop = sorted(chat.items(), key=lambda x: x[1], reverse=True)
	msg = "Статистика пользователей: \n"
	for i in range(10):
		try:
			un = unames.get(sorttop[i][0], "Unknown user {}".format(sorttop[i][0]))
		except IndexError:
			break
		msg += "{}: {} сообщений, {} {e}\n".format(un, sorttop[i][1], carma[chat_id].get(sorttop[i][0],
			defaultUserCarma), e=coinEmoji)
	try:
		bot.sendMessage(update.message.from_user.id, text=msg)
	except:
		bot.sendMessage(update.message.chat_id, text="Невозможно отправить сообщение. Напиши в ЛС мне",
			reply_to_message_id=update.message.message_id)

def ask(bot, update, args):
	chat_id = update.message.chat_id
	fail = False
	try:
		arg = int(args[0])
	except:
		fail = True

	if fail:
#		bot.sendMessage(chat_id, text="Использование: /ask <сумма>", reply_to_message_id=update.message.message_id)
		return
	else:
		toid = update.message.from_user.id
		if arg < 0:
			arg = -arg
		arg = int(arg % transferLimit)

	templ = 'asked:{}:{}'

	kbrd = [[InlineKeyboardButton("Подарить", callback_data=templ.format(toid, arg))], 
			[InlineKeyboardButton("Закончить сбор", callback_data=templ.format(toid, 'stop'))]]
	mrkup = InlineKeyboardMarkup(kbrd)

	captstr = ''
	if len(args) > 1:
		captstr = "\nКомментарий: "
		args.pop(0)
		captstr += ' '.join(args)

	bot.sendMessage(chat_id, text="{0} просит {1} {e}.{2}".format(getuname(update.message.from_user), arg, 
		captstr, e=coinEmoji), reply_markup=mrkup)

def pay(bot, update, args):
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
#		bot.sendMessage(chat_id, text="Использование: (в ответ на сообщение получателя) /pay <сумма>", 
			reply_to_message_id=update.message.message_id)
		return
	else:
		toid = update.message.reply_to_message.from_user.id
		if arg < 0:
			arg = -arg
		arg = int(arg % transferLimit)
	
	if toid == botid:
		toid = creatorid

	if not payment(chat_id, fromid, toid, arg, True):
		bot.sendMessage(chat_id, text="Недостаточно {e}!".format(e=coinEmoji),
			reply_to_message_id=update.message.message_id)
	else:
		bot.sendMessage(chat_id, text="{} {e} переведено.".format(arg, e=coinEmoji),
			reply_to_message_id=update.message.message_id)
	sendnotif(bot, fromid, toid, arg)
		
def thnx(bot, update):
	chat_id = update.message.chat_id
	if not bool(update.message.reply_to_message):
#		bot.sendMessage(chat_id, text="Использование: (в ответ на сообщение получателя) /thanks", 
#			reply_to_message_id=update.message.message_id)
		return
	u = update.message.reply_to_message.from_user
	if u.id == update.message.from_user.id:
#		bot.sendMessage(chat_id, text="Жулик, не воруй!", reply_to_message_id=update.message.message_id)
		return
	elif u.id == botid:
		u.id = creatorid
	payment(chat_id, 0, u.id, 1)
	sendnotif(bot, 0, u.id, 1)
#	bot.sendMessage(chat_id, text="Добавлено +1 {e} {0}".format(getuname(u), e=coinEmoji),
#		reply_to_message_id=update.message.message_id)

def statusupdate(bot, update):
	if not bool(update.message.new_chat_member):
		return
	if update.message.new_chat_member.id == botid:
		start(bot, update, [])

def subscr(bot, update):
	chat_id = update.message.chat_id
	from_user = update.message.from_user
	if not from_user.id in subscribed:
		try:
			bot.sendMessage(from_user.id, text='Подписка оформлена')
		except:
			bot.sendMessage(chat_id, text="Невозможно подписаться на обновления. Напишите в ЛС боту",
				reply_to_message_id=update.message.message_id)
			return
		subscribed.append(from_user.id)
		bot.sendMessage(chat_id, text="""Успешно подписаны на обновления {e}.
!Внимание! Если вы не написали боту в ЛС, вы не сможете получать уведомления""".format(e=coinEmoji),
			reply_to_message_id=update.message.message_id)
	else:
		bot.sendMessage(chat_id, text="Вы уже подписаны на обновления.", reply_to_message_id=update.message.message_id)

def unsubscr(bot, update):
	chat_id = update.message.chat_id
	from_user = update.message.from_user
	if from_user.id in subscribed:
		subscribed.pop(subscribed.index(from_user.id))
		bot.sendMessage(chat_id, text="Успешно отписаны от обновлений {e}.".format(e=coinEmoji), 
			reply_to_message_id=update.message.message_id)
	else:
		bot.sendMessage(chat_id, text="Вы ещё не подписаны на обновления.", reply_to_message_id=update.message.message_id)

def uid(bot, update):
	if bool(update.message.reply_to_message):
		uid = update.message.reply_to_message.from_user.id
	else:
		uid = update.message.from_user.id
	bot.sendMessage(update.message.chat_id, text="UID: {0}, GID: {1}".format(uid, update.message.chat_id), 
		reply_to_message_id=update.message.message_id)

def whois(bot, update, args):
	try:
		whoid = int(args[0])
	except:
		bot.sendMessage(update.message.chat_id, text="Использование: /whois UID",
			reply_to_message_id=update.message.message_id)
		return

	who = bot.getChat(whoid)
	bot.sendMessage(update.message.chat_id, text="Whois {}: Username: {}, FirstName: {}, LastName: {}".format(who.id,
		who.username, who.first_name, who.last_name), reply_to_message_id=update.message.message_id)
		
def perdolingtime(bot, update):
	bot.sendMessage(update.message.chat_id, text="It's perdoling time!", reply_to_message_id=update.message.message_id)

def codingtime(bot, update):
	bot.sendMessage(update.message.chat_id, text="It's coding time!", reply_to_message_id=update.message.message_id)

updater = Updater(TOKEN)
del TOKEN

jobs = updater.job_queue
lbot = updater.bot

jobs.put(Job(jobhourly, 3600.0))
jobs.put(Job(jobdaily, 86400.0))

#lbot.sendMessage(dbgcid, text="Hello!")
botuname = lbot.getMe().username

baselink = 'telegram.me/{un}?start='.format(un=botuname)
baselink = baselink + '{}'

dp = updater.dispatcher

##########
dp.add_handler(CommandHandler('start', start, pass_args=True))
dp.add_handler(CommandHandler('help', Help))
dp.add_handler(CommandHandler('about', about))
dp.add_handler(CommandHandler('hid', hid))
##########
dp.add_handler(CommandHandler('uid', uid))
##########
dp.add_handler(CommandHandler('whois', whois, pass_args=True))
##########
# dp.add_handler(CommandHandler('mystat', mystat, pass_args=True))
dp.add_handler(CommandHandler('st', mystat))
##########
# dp.add_handler(CommandHandler('topstat', topstat))
dp.add_handler(CommandHandler('top', topstat))
##########
# dp.add_handler(CommandHandler('msgtopstat', mtopstat))
dp.add_handler(CommandHandler('mtop', mtopstat))
##########
dp.add_handler(CommandHandler('ask', ask, pass_args=True))
##########
dp.add_handler(CommandHandler('pay', pay, pass_args=True))
##########
# dp.add_handler(CommandHandler('thanks', thnx))
dp.add_handler(CommandHandler('tx', thnx))
dp.add_handler(RegexHandler('^\+{2,}(.+)?', thnx))
##########
dp.add_handler(CommandHandler('subscr', subscr))
dp.add_handler(CommandHandler('sub', subscr))
##########
dp.add_handler(CommandHandler('unsubscr', unsubscr))
dp.add_handler(CommandHandler('unsub', unsubscr))
##########
dp.add_handler(CommandHandler('admin', adminpanel, pass_args=True))
##########
dp.add_handler(CommandHandler('tipidor', pidr))
dp.add_handler(CommandHandler('pidor', pidr))
dp.add_handler(CommandHandler('pidr', pidr))
dp.add_handler(RegexHandler('^What time is it\?$', codingtime))
dp.add_handler(RegexHandler('^Wh\u0430t time is it\?$', perdolingtime))
##########
dp.add_handler(CallbackQueryHandler(button))
dp.add_handler(MessageHandler([Filters.status_update], statusupdate))
##########
dp.add_handler(MessageHandler([], onStuff))
##########
dp.add_error_handler(error)

if path.exists(ddr + 'msg.pkl'):
	with open(ddr + 'msg.pkl', 'rb') as f:
		msgcount = pickle.load(f)
	with open(ddr + 'carma.pkl', 'rb') as f:
		carma = pickle.load(f)
	with open(ddr + 'unames.pkl', 'rb') as f:
		unames = pickle.load(f)
	with open(ddr + 'subs.pkl', 'rb') as f:
		subscribed = pickle.load(f)
	with open(ddr + 'admins.pkl', 'rb') as f:
		chatadmins = pickle.load(f)
	with open(ddr + 'targets.pkl', 'rb') as f:
		targets = pickle.load(f)
	logging.info("data loaded.")

updater.start_polling()
updater.idle()

jobhourly(None, None)

#lbot.sendMessage(dbgcid, text="Shutting down...")