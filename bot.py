# -*- coding: utf-8 -*-
# from telegram import *
# from telegram.ext import *
import telebot
from bottoken import TOKEN, creatorid
from os import path
import logging, time, math, cpickle
#import json

TIME_FORMAT = "%d %b, %H:%M:%S"
logging.basicConfig(format = '%(levelname)-8s [%(asctime)s] %(message)s', level = logging.INFO,
    datefmt = TIME_FORMAT)

botid = int(TOKEN[:TOKEN.index(':')])

help_text = """Привет. Я ̶н̶е̶̶д̶о̶бот, который считает ₫ (карму) в чате :)
/mystat или /st — узнать статистику пользователя
/topstat или /top — топ пользователей по ₫
/msgtopstat или /mtop — топ пользователей по сообщениям
/pay — перевести ₫
/ask — попросить ₫
++ — +1 ₫ другого человека
/sub или /subscr — подписаться на изменения ₫ (сообщения приходят в ЛС)
Для отписки — /unsub или /unsubscr

Каждый день самым активным пользователям чата — призы!
за 0 место - +овер9к ₫
За 1 место — +10 ₫
За 2 место — +5 ₫
За 3 место — +2 ₫
_____
Ограничение всех переводов: [0..1023]
Инфо о ̶н̶е̶боте —> /about
Команды ̶н̶е̶администрирования —> /admin
Вскоре ̶̶н̶е̶будут доступны некоторые ̶н̶е̶плюшки с тратой ₫, а пока, зарабатывайте её!"""

hid_text = """Команды, не относящиеся непосредственно к боту:
/uid — узнать UID и GID
/whois — узнать, кто владелец определённого ID
/pidor — feature by @mrsteyk (modified original concept /crack)
/duck — feature by @mrsteyk
"""

about_text = """Я бот, который считает ₫ в чате :)
По всем вопросам, обращайся к моему создателю —> @mrsteyk
Если вы хотите помочь написанию бота (или просто посмотреть какой хуйнёй мы маемся), вам сюда —> @itcat_carma"""

features_text = """Фичи за ₫ (WIP):
Название - Цена - Как получить
Досрочный разбан - 50 - /feature 0
Отправка сообщения во время бана - 5 - /feature 1
Передать всем привет - 1 - /feature 2
Получить подарок на праздник - (-2) - /feature 3
Устроить раздачу - 100 - /feature 4
Уметь отнимать ₫ - 1000 - /feature 5
Быть ₫рочером - 500 - /feature 6"""

#defaultAdminCarma = -20
defaultUserCarma = 9001 # ITS OVER 9K!!! Dragon Ball Z reference
addViaThanks = 1006 # why its even here?
transferLimit = 1024

# filters = [Filters.audio,
#   Filters.contact,
#   Filters.command,
#   Filters.document,
#   Filters.location,
#   Filters.photo,
#   Filters.status_update,
#   Filters.sticker,
#   Filters.text,
#   Filters.venue,
#   Filters.video,
#   Filters.voice]

carma = {}
msgcount = {}
unames = {}
chatadmins = {}
subscribed = []
#bank = {}

# --- Not commands start ---

def error(bot, update, error):
    logging.warning('Update "{0}" caused error "{1}"'.format(update, error)) # dat line fucks up my sublime text 3
    bot.send_message(update.message.chat_id, text="Произошла ошибка при обработке этого сообщения (возможно юзверь не написал боту в личку, но подписался на обновления)", 
        reply_to_message_id=update.message.message_id)

def payment(chat_id, from_id, to_id, amount, check=False): # payment(chat_id, from_id, to_id, amount, check=False) wtf is check?
    global carma
    fromcarma = carma[chat_id].get(from_id, defaultUserCarma)
    if check and amount > fromcarma: # прям сука очень хорошее сравнение дан бай евгфилим1
        return False
    if from_id != 0:
        carma[chat_id][from_id] = fromcarma - amount
    if to_id != 0:
        carma[chat_id][to_id] = carma[chat_id].get(to_id, defaultUserCarma) + amount

    return True

def sendnotif(bot, from_id, to_id, amount): # #ZebestUseOfMultiples! 
    if from_id != 0 and from_id in subscribed:
        capt = ''
        if to_id != 0:
            capt = 'для пользователя {}'.format(unames.get(to_id, 'Неизвестный юзверь {}'.format(to_id)))
        bot.send_message(from_id, text="У вас было отнято {} ₫ {}".format(amount, capt))
        del capt

    if to_id != 0 and to_id in subscribed:
        capt = ''
        if from_id != 0:
            capt = 'пользователем {}'.format(unames.get(from_id, 'Неизвестный юзверь {}'.format(from_id)))
        bot.send_message(to_id, text="Вам было добавлено {} ₫ {}".format(amount, capt))

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


def jobdaily(bot, job): # why args???
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
            bonus = bonus // 2

    for chat in msgcount:
        msgcount[chat].clear()

def jobhourly(bot, job): # why args???x2
    with open('msg.pkl', 'wb') as f:
        cpickle.dump(msgcount, f, 2)
    with open('carma.pkl', 'wb') as f:
        cpickle.dump(carma, f, 2)
    with open('unames.pkl', 'wb') as f:
        cpickle.dump(unames, f, 2)
    with open('subs.pkl', 'wb') as f:
        cpickle.dump(subscribed, f, 2)
    with open('admins.pkl', 'wb') as f:
        cpickle.dump(chatadmins, f, 2)
    logging.info("data saved.")

# --- Not commands end? ---

@bot.message_handler(commands=['start'])
def start(message):
    global carma, msgcount, chatadmins, unames
    chat_id = message.chat_id
    args = string(message.text).split()
    args.pop(0)
    if chat_id == message.from_user.id:
        bot.send_message(chat_id, "Готово, теперь вы можете получать уведомления.")
        return

    if chat_id in carma:
        if len(args) == 1 and args[0] == 'clear' and update.message.from_user.id == creatorid:
            bot.reply_to(message, "Реинициализация чата...")
        else:
            bot.reply_to(message, "Этот чат уже инициализирован")
            return
    carma[chat_id] = {}
    msgcount[chat_id] = {}
    chatadmins[chat_id] = []
    admins = bot.getChatAdministrators(chat_id)
    for admin in admins:
        #carma[chat_id].update({admin.user.id: defaultAdminCarma})
        #msgcount[chat_id].update({admin.user.id: 0})
        unames.update({admin.user.id: getuname(admin.user)})
        chatadmins[chat_id].append(admin.user.id)

    bot.send_message(chat_id, "Чат инициализирован. /help")

@bot.message_handler(commands=['help'])
def Help(message):
    bot.send_message(message.chat_id, help_text)

@bot.message_handler(commands=['about'])
def about(message):
    bot.send_message(message.chat_id, about_text)

@bot.message_handler(commands=['hid'])
def hid(message):
    bot.send_message(message.chat_id, hid_text)

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
                bot.edit_message_text("Сбор ₫ остановлен владельцем.", chat_id=chat_id, message_id=msg_id, reply_markup=InlineKeyboardMarkup([]))
            else:
                bot.answer_callback_query(inlmsgid, text="Вы не владелец этого сбора ₫")
        else:
            if payment(chat_id, qfrom, int(data[1]), int(data[2]), True):
                bot.answer_callback_query(callback_query_id=inlmsgid, text="Успешно переведено {} ₫".format(data[2]))
                sendnotif(bot, qfrom, int(data[1]), int(data[2]))
            else:
                bot.answer_callback_query(inlmsgid, text="Недостаточно ₫")
    else:
        return

@bot.message_handler(commands=['admin'])
def adminpanel(message):
    global carma, msgcount, unames, chatadmins, subscribed
    args = string(message.text).split()
    args.pop(0) # ?maybe? can be improved
    chat_id = message.chat_id
    from_id = message.from_user.id
    if from_id not in chatadmins[chat_id] and from_id != creatorid:
        bot.reply_to(message, "Недостаточно прав")
        return

    if len(args) == 0:
        bot.reply_to(message, """Available commands:
flush\nspin\nreinit\ngivecarma\nsetcarma\ntakecarma""")

    else:
        cmd = args[0]
        args.pop(0)
        if cmd == 'flush':
            jobhourly(None, None)
            bot.reply_to(message, "jobhourly done")
            return
        elif cmd == 'spin':
            jobdaily(None, None)
            bot.reply_to(message, "jobdaily done")
            return
#       elif cmd == 'dbgvar':
#           bot.send_message(chat_id, text='{}'.format(eval(args[0])))
#           return
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
                bot.reply_to(message, "Usage: /admin reinit [all|carma|msgcount|unames|chatadmins|subscribed]")
            bot.reply_to(message, "{} done".format(cmd + args[0]))
            return
        elif cmd == 'givecarma':
            try:
                toid = int(args[0])
                amount = int(args[1])
            except:
                bot.send_message(chat_id, text="Usage: /admin givecarma <to_id> <amount>")
                return
            fromid = 0
            bot.reply_to(message, "{} done".format(cmd))
        elif cmd == 'setcarma':
            try:
                toid = int(args[0])
                amount = int(args[1])
            except:
                bot.send_message(chat_id, text="Usage: /admin setcarma <to_id> <amount>")
                return
            carma[chat_id][toid] = amount
            bot.reply_to(message, "{} done".format(cmd))
            return
        elif cmd == 'takecarma':
            try:
                fromid = int(args[0])
                amount = int(args[1])
            except:
                bot.send_message(chat_id, "Usage: /admin takecarma <to_id> <amount>")
                return
            toid = 0
            bbot.reply_to(message, "{} done".format(cmd))

        payment(chat_id, fromid, toid, amount) # wtf???
        sendnotif(bot, fromid, toid, amount)   # wtf???x2

@bot.message_handler(commands=['st', 'mystat'])
def mystat(message):
    if bool(message.reply_to_message):
        uu = message.reply_to_message.from_user
        uid = uu.id
    else:
        uu = message.from_user
        uid = uu.id
    text = """Статистика пользователя {u}:
₫: {c}
Сообщений за день: {m}""".format(u=getuname(uu), c=carma[message.chat_id].get(uid, defaultUserCarma), m=msgcount[message.chat_id].get(uid, 0))

    bot.reply_to(message, text)

@bot.message_handler(commands=['top', 'topstat'])
def topstat(message):
    chat_id = message.chat_id
    chat = carma[chat_id]
    sorttop = sorted(chat.items(), key=lambda x: x[1], reverse=True)
    msg = "Статистика пользователей: \n"
    for i in range(10):
        try:
            un = unames.get(sorttop[i][0], "Unknown user {}".format(sorttop[i][0]))
        except IndexError:
            break
        msg += "{}: {} сообщений, {} ₫\n".format(un, msgcount[chat_id].get(sorttop[i][0], 0), sorttop[i][1])
    bot.send_message(chat_id, msg)

@bot.message_handler(commands=['mtop' , 'msgtopstat'])
def mtopstat(message):
    chat_id = message.chat_id
    chat = msgcount[chat_id]
    sorttop = sorted(chat.items(), key=lambda x: x[1], reverse=True)
    msg = "Статистика пользователей: \n"
    for i in range(10):
        try:
            un = unames.get(sorttop[i][0], "Unknown user {}".format(sorttop[i][0]))
        except IndexError:
            break
        msg += "{}: {} сообщений, {} ₫\n".format(un, sorttop[i][1], carma[chat_id].get(sorttop[i][0], defaultUserCarma))
    bot.send_message(chat_id, msg)

@bot.message_handler(commands=['ask'])
def ask(message): # not done
    args = message.text
    args = args.split()
    args.pop(0)
    chat_id = update.message.chat_id
    fail = False
    try:
        arg = int(args[0])
    except:
        fail = True

    if fail:
        bot.reply_to(message, "Использование: /ask <сумма>")
        return
    else:
        toid = message.from_user.id
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

    bot.send_message(chat_id, "{} просит {} ₫.{}".format(getuname(update.message.from_user), arg, captstr), reply_markup=mrkup)

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
        bot.send_message(chat_id, text="Использование: (в ответ на сообщение получателя) /pay <сумма>", 
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
        bot.send_message(chat_id, text="Недостаточно ₫!", reply_to_message_id=update.message.message_id)
    else:
        bot.send_message(chat_id, text="{} ₫ переведено.".format(arg), reply_to_message_id=update.message.message_id)
    sendnotif(bot, fromid, toid, arg)
        
def thnx(bot, update):
    chat_id = update.message.chat_id
    if not bool(update.message.reply_to_message):
#       bot.send_message(chat_id, text="Использование: (в ответ на сообщение получателя) /thanks", 
#           reply_to_message_id=update.message.message_id)
        return
    u = update.message.reply_to_message.from_user
    if u.id == update.message.from_user.id:
#       bot.send_message(chat_id, text="Жулик, не воруй!", reply_to_message_id=update.message.message_id)
        return
    elif u.id == botid:
        u.id = creatorid
    payment(chat_id, 0, u.id, 1)
    sendnotif(bot, 0, u.id, 1)
#   bot.send_message(chat_id, text="Добавлено +1 к карме {}".format(getuname(u)),
#       reply_to_message_id=update.message.message_id)

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
            bot.send_message(from_user.id, text='Подписка оформлена')
        except:
            bot.send_message(chat_id, text="Невозможно подписаться на обновления. Напишите в ЛС боту",
            reply_to_message_id=update.message.message_id)
            return
        subscribed.append(from_user.id)
        bot.send_message(chat_id, text="""Успешно подписаны на обновления ₫.
!Внимание! Если вы не написали боту в ЛС, вы не сможете получать уведомления""", reply_to_message_id=update.message.message_id)
    else:
        bot.send_message(chat_id, text="Вы уже подписаны на обновления.", reply_to_message_id=update.message.message_id)

def unsubscr(bot, update):
    chat_id = update.message.chat_id
    from_user = update.message.from_user
    if from_user.id in subscribed:
        subscribed.pop(subscribed.index(from_user.id))
        bot.send_message(chat_id, text="Успешно отписаны от обновлений ₫.", 
            reply_to_message_id=update.message.message_id)
    else:
        bot.send_message(chat_id, text="Вы ещё не подписаны на обновления.", reply_to_message_id=update.message.message_id)

@bot.message_handler(commands=['uid'])
def uid(message):
    if bool(message.reply_to_message):
        uid = message.reply_to_message.from_user.id
    else:
        uid = message.from_user.id
    bot.reply_to(message, "UID: {0}, GID: {1}".format(uid, message.chat_id))

@bot.message_handler(commands=['whois'])
def whois(message):
    try:
        whoid = int(string(message).split()[1])
    except:
        bot.reply_to(message, "Использование: /whois UID")
        return

    who = bot.getChat(whoid)
    bot.reply_to(message, "Whois {}: Username: {}, FirstName: {}, LastName: {}".format(who.id, who.username, who.first_name, who.last_name))

@bot.message_handler(commands=['pidr'])
def pidr(message):
    # onStuff(bot, update)
    # payment(update.message.chat_id, update.message.from_user.id, 0, 100)
    # WIP

#updater = Updater(TOKEN) No Real Need Since there is no way to obtain a var value
#del TOKEN

# jobs = updater.job_queue WIP

# jobs.put(Job(jobhourly, 3600.0))
# jobs.put(Job(jobdaily, 86400.0))

# dp = updater.dispatcher

##########
# dp.add_handler(CommandHandler('start', start, pass_args=True))
# dp.add_handler(CommandHandler('help', Help)) done
# dp.add_handler(CommandHandler('about', about)) done
# dp.add_handler(CommandHandler('hid', hid)) done
##########
# dp.add_handler(CommandHandler('uid', uid)) done 
##########
# dp.add_handler(CommandHandler('whois', whois, pass_args=True)) done
##########
# dp.add_handler(CommandHandler('mystat', mystat))
# dp.add_handler(CommandHandler('st', mystat))
##########
# dp.add_handler(CommandHandler('topstat', topstat))
# dp.add_handler(CommandHandler('top', topstat))
########## done
# dp.add_handler(CommandHandler('msgtopstat', mtopstat))
# dp.add_handler(CommandHandler('mtop', mtopstat))
##########
dp.add_handler(CommandHandler('ask', ask, pass_args=True))
##########
dp.add_handler(CommandHandler('pay', pay, pass_args=True))
##########
dp.add_handler(CommandHandler('thanks', thnx))
dp.add_handler(CommandHandler('tx', thnx))
dp.add_handler(RegexHandler('^\+{2,}(.+)?', thnx))
##########
dp.add_handler(CommandHandler('subscr', subscr))
dp.add_handler(CommandHandler('sub', subscr))
##########
dp.add_handler(CommandHandler('unsubscr', unsubscr))
dp.add_handler(CommandHandler('unsub', unsubscr))
##########
# dp.add_handler(CommandHandler('admin', adminpanel, pass_args=True)) done
##########
dp.add_handler(CallbackQueryHandler(button))
dp.add_handler(MessageHandler([Filters.status_update], statusupdate))
##########
dp.add_handler(MessageHandler([], onStuff))
##########
dp.add_error_handler(error)

if path.exists('msg.pkl'):
    with open('msg.pkl', 'rb') as f:
        msgcount = cpickle.load(f)
    with open('carma.pkl', 'rb') as f:
        carma = cpickle.load(f)
    with open('unames.pkl', 'rb') as f:
        unames = cpickle.load(f)
    with open('subs.pkl', 'rb') as f:
        subscribed = cpickle.load(f)
    with open('admins.pkl', 'rb') as f:
        chatadmins = cpickle.load(f)
    logging.info("data loaded.")

updater.start_polling()
updater.idle()

jobhourly(None, None)
