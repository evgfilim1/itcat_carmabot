# -*- coding: utf-8 -*-

import datetime
import logging
import pickle
from os import path
from random import randint

from telegram import *
from telegram.ext import *

import botlibs.settings as botset

ddr = './botdata/'

TIME_FORMAT = "%d %b, %H:%M:%S"
LOG_FORMAT = '%(levelname)-8s [%(asctime)s] %(message)s'
logging.basicConfig(format=LOG_FORMAT, level=logging.DEBUG,
                    filename="{}bot.log".format(ddr), datefmt=TIME_FORMAT)

botid = int(botset.TOKEN[:botset.TOKEN.index(':')])

coinEmoji = botset.coin
msgEmoji = botset.msg
ticketEmoji = botset.ticket

help_text = """Привет. Я бот, который считает catcoin'ы (обозначаются как {e}) в чате :)
/st — узнать статистику пользователя
/top — топ пользователей по {e}
/mtop — топ пользователей по {m}
/ft или /feature — потратить карму
/gf или /gifter — устроить раздачу (made by @metroyanno)
/pay — перевести {e}
/ask — попросить {e}
/tx или "+" — +1 {e} для другого человека
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
Теперь (НАКОНЕЦ-ТО!!!) доступны фичи для траты кармы
""".format(e=coinEmoji, m=msgEmoji)

hid_text = """Команды, не относящиеся непосредственно к боту:
/uid — узнать UID и GID
/whois — узнать, кто владелец определённого ID
Коты ван лав!
"""

about_text = """Я бот, который считает {e} в чате :)
Изменения в последней версии: /whatsnew
По всем вопросам, обращайся к моему создателю —> @evgfilim1
Если вы хотите помочь написанию бота, вам сюда —> @itcat_carma""".format(e=coinEmoji)

features_text = """Фичи за {e}:
Название - Цена - Как получить
Отправка сообщения во время бана - 5 - /feature 1
Передать всем привет - 1 - /feature 2
Получить подарок на праздник - (-10) - /feature 3
Получить старт кит - 0 - /feature 4
Испытать удачу (by @evgfilim1) - 0||5 - /feature 7
Испытать удачу (by @metroyanno) - 5 - /feature 777
""".format(e=coinEmoji)

defaultUserCarma = 0
addViaThanks = 1
transferLimit = 1024
bonusSize = 10
ftStartkitsize = 30

ftHolylist = {(30, 12): "С днём рождения IT-Koта!", (31, 12): "С наступающим Новым годом!",
              (1, 1): "С Новым годом!!!", (23, 2): "С днём защитника Отечества!", (1, 3): "С днём кошечек!",
              (8, 3): "С Восьмым марта!", (4, 4): "? ???? ??????????!", (1, 5): "С днём Весны и Труда!",
              (9, 5): "С днём Победы!", (12, 6): "С днём России!", (1, 9): "С днём знаний!!1)0)))",
              (13, 9): "while True: print('С праздником, программисты!\n')", (5, 10): "С днём учителя!",
              (4, 11): "С днём народного единства!"}

ftStartkit = {}
ftTestluck = {}
ftHolidaygot = {}

randSave = {}

carma = {}
msgcount = {}
unames = {}
chatadmins = {}
subscribed = []
targets = {}
giftbank = {}


def error_handler(bot, update, error):
    logging.warning('Update "{0}" caused error "{1}"'.format(update, error))
    bot.sendMessage(update.message.chat_id, text="Произошла ошибка при обработке этого сообщения",
                    reply_to_message_id=update.message.message_id)


def whatsnew(bot, update):
    t = """Что нового в версии 3.2?
1) Исправлен формат логов ({})
2) Оптимизирован алгоритм рандома по команде /feature 7
3) Временно выпилены: раздатчик (/gifter), лотерея (/feature 777)
4) Теперь шанс выпадения отрицательного бонуса /ft 7 уменьшен с 53% до 31%
5) Теперь при смене чата (с группы на супергруппу) бот переместит данные предыдущего чата в новый [todo]
0) Проведён рефакторинг кода
""".format(botset.loggingChannel)

    bot.sendMessage(update.message.chat_id, text=t)


def timediff():
    t = botset.whenspin.split(':')
    now = datetime.datetime.now()
    then = datetime.datetime(2016, 1, 1, int(t[0]), int(t[1]))
    diff = then - now
    delta = float(diff.seconds) + (diff.microseconds / 10 ** 6)
    return delta


def payment(chat_id, from_id, to_id, amount, check=True):
    fromcarma = carma[chat_id].get(from_id, defaultUserCarma)
    if from_id != 0 and check and amount > fromcarma:
        return False
    if from_id != 0:
        carma[chat_id][from_id] = fromcarma - amount
    if to_id != 0:
        carma[chat_id][to_id] = carma[chat_id].get(to_id, defaultUserCarma) + amount

    return True


def sendnotif(bot, from_id, to_id, amount, chat_id, *, txfrom=0, bankcapt=""):
    chatinfo = bot.getChat(chat_id).title
    if from_id != 0:
        frominfo = unames.get(from_id, getuname(bot.getChat(from_id)))
    elif txfrom != 0:
        from_id = txfrom
        frominfo = unames.get(from_id, getuname(bot.getChat(from_id)))
    else:
        frominfo = "Bank"
    if to_id != 0:
        toinfo = unames.get(to_id, getuname(bot.getChat(to_id)))
    else:
        toinfo = "Bank"

    if from_id != 0 and from_id in subscribed:
        capt = ''
        if to_id != 0:
            capt = 'для пользователя {}'.format(unames.get(to_id, 'Unknown user {}'.format(to_id)))
        bot.sendMessage(from_id, text="У вас было отнято {0} {e} {1} в чате {2}".format(amount, capt, chatinfo,
                                                                                        e=coinEmoji))
        del capt

    if to_id != 0 and to_id in subscribed:
        capt = ''
        if txfrom != 0:
            bot.sendMessage(to_id,
                            text="Вас поблагодарил(а) {1} в чате {0}".format(chatinfo,
                                                                             unames.get(txfrom,
                                                                                        "Unknown user {i}".format(
                                                                                            i=txfrom))))
        else:
            if from_id != 0:
                capt = 'пользователем {}'.format(unames.get(from_id, 'Unknown user {}'.format(from_id)))
            bot.sendMessage(to_id, text="Вам было добавлено {0} {e} {1} в чате {2}".format(amount, capt, chatinfo,
                                                                                           e=coinEmoji))

    if botset.useLoggingChannel:
        c = ""
        te = """Chat ID: {} ({})\nFrom ID: {} ({})
To ID: {} ({})\nComment: {comment}\nAmount: {}\n\nTime:{}"""
        if txfrom != 0:
            c = "by '+'"
        elif (from_id == 0) or (to_id == 0):
            c = bankcapt
        dt = datetime.datetime.now()
        f = (chat_id, chatinfo, from_id, frominfo, to_id, toinfo, amount, dt)
        bot.sendMessage(botset.loggingChannel, text=te.format(*f, comment=c))


def get_top(chat_id, *, messages):
    if not messages:
        chat = carma[chat_id]
        second = msgcount[chat_id]
        es = (coinEmoji, msgEmoji)
        defvar = defaultUserCarma
    else:
        chat = msgcount[chat_id]
        second = carma[chat_id]
        es = (msgEmoji, coinEmoji)
        defvar = 0

    sorttop = sorted(chat.items(), key=lambda x: x[1], reverse=True)
    msg = "Статистика пользователей: \n"
    for i in range(10):
        try:
            un = unames.get(sorttop[i][0], "Unknown user {}".format(sorttop[i][0]))
        except IndexError:
            break
        msg += "{0}: {1} {e}, {2} {m}\n".format(un, sorttop[i][1], second.get(sorttop[i][0], defvar),
                                                e=es[0], m=es[1])
    return msg


def getuname(user):
    if bool(user.username):
        return '@' + user.username
    else:
        return user.first_name


def inprivate(chat_id, from_id):
    return chat_id == from_id


def api_inprivate(bot, chat_id):
    return bot.getChat(chat_id).type == 'private'


def api_isadmin(bot, user_id):
    return


def randomstuff():
    u = randint(0, 1)
    r = randint(0, 2)
    v = randint(0, 2)
    s = randint(0, 2)

    # optimized by @coder_ilya_gavrilov
    if u != 0:
        return randint(-9, 5)
    if r != 0:
        return randint(5, 16)
    if v != 0:
        return randint(17, 30)
    if s != 0:
        return randint(31, 50)
    return randomstuff()


def on_stuff(bot, update):
    # global msgcount, unames
    uid = update.message.from_user.id
    gid = update.message.chat_id
    if inprivate(gid, uid):
        return
    msgcount[gid][uid] = msgcount[gid].get(uid, 0) + 1
    if uid not in carma[gid]:
        carma[gid][uid] = defaultUserCarma
    unames.update({uid: getuname(update.message.from_user)})


def jobdaily(bot, job):
    # global msgcount
    for cid in msgcount:
        chat = msgcount[cid]
        sorttop = sorted(chat.items(), key=lambda x: x[1], reverse=True)
        bonus = bonusSize
        for u in range(3):
            try:
                usrid = sorttop[u][0]
            except IndexError:
                break
            carma[cid][usrid] = carma[cid].get(usrid, 0) + bonus
            sendnotif(bot, 0, usrid, bonus, cid, bankcapt="daily gift")
            bonus //= 2

    for chat in msgcount:
        msgcount[chat].clear()

    for chat in ftHolidaygot:
        ftHolidaygot[chat].clear()

    for chat in ftTestluck:
        ftTestluck[chat].clear()

    logging.info("jobdaily done")


def loader(filename):
    with open(ddr + filename, 'rb') as ff:
        return pickle.load(ff)


def saver(obj, filename):
    with open(ddr + filename, 'wb') as ff:
        pickle.dump(obj, ff, pickle.HIGHEST_PROTOCOL)


def loaddata():
    global msgcount, carma, unames, subscribed, chatadmins, targets
    global giftbank, randSave, ftHolidaygot, ftTestluck, ftStartkit
    if path.exists(ddr + 'msg.pkl'):
        # optimized by @coder_ilya_gavrilov
        msgcount = loader('msg.pkl')
        carma = loader('carma.pkl')
        unames = loader('unames.pkl')
        subscribed = loader('subs.pkl')
        chatadmins = loader('admins.pkl')
        targets = loader('targets.pkl')
        giftbank = loader('giftbank.pkl')
        randSave = loader('rand.pkl')
        ftHolidaygot = loader('fthol.pkl')
        ftTestluck = loader('ftluck.pkl')
        ftStartkit = loader('kit.pkl')

        logging.info("data loaded.")


def jobhourly(bot, job):
    saver(msgcount, 'msg.pkl')
    saver(carma, 'carma.pkl')
    saver(unames, 'unames.pkl')
    saver(subscribed, 'subs.pkl')
    saver(chatadmins, 'admins.pkl')
    saver(targets, 'targets.pkl')
    saver(giftbank, 'giftbank.pkl')
    saver(randSave, 'rand.pkl')
    saver(ftHolidaygot, 'fthol.pkl')
    saver(ftTestluck, 'ftluck.pkl')
    saver(ftStartkit, 'kit.pkl')

    logging.info("data saved.")


def start(bot, update, args):
    # if not (len(args) == 1 and args[0] == 'joingroup'):
        # text = update.message.text.split()[0].split('@')
        # if not ((len(text) == 2 and text[1] == botuname) or (len(text) == 1)):
            # return

    try:
        target = int(args[0])
    except (IndexError, ValueError):
        target = None

    chat_id = update.message.chat_id
    from_id = update.message.from_user.id

    if inprivate(chat_id, from_id):
        if target:
            ct = bot.getChat(target)
            if ct.type == 'private':
                bot.sendMessage(chat_id, text="Я не умею считать {e} в ЛС.".format(e=coinEmoji))
                return
            targets.update({from_id: target})
            bot.sendMessage(chat_id, text="'{}' установлен как чат по умолчанию".format(ct.title))
            return
        else:
            bot.sendMessage(chat_id, text="""Готово, теперь вы можете получать уведомления.

Если вы хотите установить чат по умолчанию в ЛС (чтобы я реагировал на команды, как в чате), {}""".format(
                "напишите в том чате /start getlink"))
            return

    if chat_id in carma:
        if len(args) > 0 and args[0] == 'clear' and update.message.from_user.id == botset.creatorid:
            bot.sendMessage(chat_id, text="Реинициализация чата...", reply_to_message_id=update.message.message_id)
        elif len(args) > 0 and args[0] == 'getlink':
            bot.sendMessage(chat_id,
                            text="[Установить этот чат в качестве чата по умолчанию в ЛС]({})".format(
                                baselink.format(chat_id)),
                            parse_mode="Markdown", disable_web_page_preview=True,
                            reply_to_message_id=update.message.message_id)
            return
        else:
            bot.sendMessage(chat_id, text="Этот чат уже инициализирован", reply_to_message_id=update.message.message_id)
            return
    carma[chat_id] = {}
    msgcount[chat_id] = {}
    chatadmins[chat_id] = []
    ftHolidaygot[chat_id] = []
    ftTestluck[chat_id] = []
    ftStartkit[chat_id] = []
    admins = bot.getChatAdministrators(chat_id)
    for admin in admins:
        unames.update({admin.user.id: getuname(admin.user)})
        chatadmins[chat_id].append(admin.user.id)

    bot.sendMessage(chat_id, text="Чат инициализирован. /help")


def help_(bot, update):
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


def ping(bot, update):
    bot.sendMessage(update.message.chat_id,
                    text="@{} ping statistics:\n4 packets transmitted, 4 received, 0% packet loss".format(botuname),
                    reply_to_message_id=update.message.message_id)


def hid(bot, update):
    try:
        bot.sendMessage(update.message.from_user.id, text=hid_text)
    except:
        bot.sendMessage(update.message.chat_id, text="Невозможно отправить сообщение. Напиши в ЛС мне",
                        reply_to_message_id=update.message.message_id)


# def async_start(bot, query, name, data, randSave, coinEmoji, chat_id):
# 	__import__("time").sleep(3)
# 	templ = 'zero:{0}:{1}'
# 	kbrd = [[InlineKeyboardButton("{e}{p}".format(p=coinEmoji, e=randSave.get(str(chat_id) + '_' + str(data) + '_1', 0)), callback_data=templ.format(data, '1'))],
# 		[InlineKeyboardButton("{e}{p}".format(p=coinEmoji, e=randSave.get(str(chat_id) + '_' + str(data) + '_2', 0)), callback_data=templ.format(data, '2'))],
# 		[InlineKeyboardButton("{e}{p}".format(p=coinEmoji, e=randSave.get(str(chat_id) + '_' + str(data) + '_3', 0)), callback_data=templ.format(data, '3'))]]
# 	mrkup = InlineKeyboardMarkup(kbrd)
# 	bot.editMessageText(chat_id=query.message.chat_id, message_id=query.message.message_id, reply_markup=mrkup, text="{e} выбрал билет.".format(e=name))
# 	__import__("time").sleep(10)
# 	bot.editMessageText(chat_id=query.message.chat_id, message_id=query.message.message_id, text="Игра закончена!")

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
            elif qfrom in chatadmins[chat_id] or qfrom == botset.creatorid:
                bot.editMessageText(chat_id=chat_id, message_id=msg_id, reply_markup=InlineKeyboardMarkup([]),
                                    text="Сбор {e} остановлен Админом.".format(e=coinEmoji))
            else:
                bot.answerCallbackQuery(callback_query_id=inlmsgid,
                                        text="Вы не владелец этого сбора {e}".format(e=coinEmoji))
        else:
            if payment(chat_id, qfrom, int(data[1]), int(data[2]), True):
                bot.answerCallbackQuery(callback_query_id=inlmsgid,
                                        text="Успешно переведено {} {e}".format(data[2], e=coinEmoji))
                sendnotif(bot, qfrom, int(data[1]), int(data[2]), chat_id)
            else:
                bot.answerCallbackQuery(callback_query_id=inlmsgid, text="Недостаточно {e}".format(e=coinEmoji))
    # elif data[0] == 'gift': ###TODO: Fix this very loooooong code
    # 	by_gift = giftbank.get(str(chat_id) + '_' + str(data[1]) + '_by',0)
    # 	if (giftbank.get(str(chat_id) + '_' + str(data[1]) + '_sum', 0) > 0) and (by_gift <= giftbank.get(str(chat_id) + '_' + str(data[1]) + '_sum', 0)):
    # 		if giftbank.get(str(chat_id) + '_' + str(data[1]) + '_' + str(qfrom), 0) == 'get':
    # 			bot.answerCallbackQuery(callback_query_id=inlmsgid, text="Ты уже получал подарок с этой раздачи!")
    # 			return
    # 		giftbank[str(chat_id) + '_' + str(data[1]) + '_sum'] = giftbank.get(str(chat_id) + '_' + str(data[1]) + '_sum', 0) - by_gift
    # 		giftbank[str(chat_id) + '_' + str(data[1]) + '_' + str(qfrom)] = 'get'
    # 		payment(chat_id, 0, qfrom, by_gift, False)
    # 		sendnotif(bot, 0, qfrom, by_gift, chat_id, bankcapt="by_gift")
    # 		bot.answerCallbackQuery(callback_query_id=inlmsgid, text="Ты получил подарок в {h}{e}!".format(e=coinEmoji, h=by_gift))
    # 		if giftbank.get(str(chat_id) + '_' + str(data[1]) + '_sum', 0) < by_gift:
    # 			payment(chat_id, 0, giftbank.get(str(chat_id) + '_' + str(data[1]) + '_back', 0), giftbank.get(str(chat_id) + '_' + str(data[1]) + '_sum', 0), False)
    # 			sendnotif(bot, 0, giftbank.get(str(chat_id) + '_' + str(data[1]) + '_back', 0), giftbank.get(str(chat_id) + '_' + str(data[1]) + '_sum', 0), chat_id, bankcapt="by gift")
    # 			del giftbank[str(chat_id) + '_' + str(data[1]) + '_sum']
    # 			del giftbank[str(chat_id) + '_' + str(data[1]) + '_by']
    # 			del giftbank[str(chat_id) + '_' + str(data[1]) + '_id']
    # 			del giftbank[str(chat_id) + '_' + str(data[1]) + '_back']
    # 			bot.editMessageText(chat_id=query.message.chat_id, message_id=query.message.message_id, text="Раздача {e} закончилась".format(e=coinEmoji))
    # 			return
    # 		from_id = giftbank.get(str(chat_id) + '_' + str(data[1]) + '_id', 0)
    # 		templ = 'gift:{}'
    # 		kbrd = [[InlineKeyboardButton("Принять подарок!", callback_data=templ.format(data[1]))]]
    # 		mrkup = InlineKeyboardMarkup(kbrd)
    # 		bot.editMessageText(chat_id=query.message.chat_id, message_id=query.message.message_id, reply_markup=mrkup, text="{0} дарит по {1}{e}. Осталось: {2}{e}".format(str(from_id), by_gift, giftbank.get(str(chat_id) + '_' + str(data[1]) + '_sum', 0), e=coinEmoji))
    # 	else:
    # 		bot.answerCallbackQuery(callback_query_id=inlmsgid, text="Выдача {e} закончена".format(e=coinEmoji))
    # 		return
    # elif data[0] == 'ticket':
    # 	if randSave.get(str(chat_id) + '_' + str(data[1]) + '_back', 0) == qfrom:
    # 		randSave[str(chat_id) + '_' + str(data[1]) + '_back'] = -1
    # 		name = randSave.get(str(chat_id) + '_' + str(data[1]) + '_name', 0)
    # 		del randSave[str(chat_id) + '_' + str(data[1]) + '_back']
    # 		templ = 'zero:{0}:{1}'
    # 		ins1 = ''
    # 		ins2 = ''
    # 		ins3 = ''
    # 		if str(data[2]) == '1':
    # 			ins1 = randSave.get(str(chat_id) + '_' + str(data[1]) + '_1', 0)
    # 			payment(chat_id, 0, qfrom, ins1, False)
    # 			kbrd = [[InlineKeyboardButton("{e}{p}".format(p=coinEmoji, e=ins1), callback_data=templ.format(data[1], '1'))],
    # 				[InlineKeyboardButton("{p}".format(p=ticketEmoji), callback_data=templ.format(data[1], '2'))],
    # 				[InlineKeyboardButton("{p}".format(p=ticketEmoji), callback_data=templ.format(data[1], '3'))]]
    # 			if int(ins1) > 0:
    # 				sendnotif(bot, 0, qfrom, ins1, chat_id, bankcapt="ticket")
    # 		elif str(data[2]) == '2':
    # 			ins2 = randSave.get(str(chat_id) + '_' + str(data[1]) + '_2', 0)
    # 			payment(chat_id, 0, qfrom, ins2, False)
    # 			kbrd = [[InlineKeyboardButton("{p}".format(p=ticketEmoji), callback_data=templ.format(data[1], '1'))],
    # 				[InlineKeyboardButton("{e}{p}".format(p=coinEmoji, e=ins2), callback_data=templ.format(data[1], '2'))],
    # 				[InlineKeyboardButton("{p}".format(p=ticketEmoji), callback_data=templ.format(data[1], '3'))]]
    # 			if int(ins2) > 0:
    # 				sendnotif(bot, 0, qfrom, ins2, chat_id, bankcapt="ticket")
    # 		elif str(data[2]) == '3':
    # 			ins3 = randSave.get(str(chat_id) + '_' + str(data[1]) + '_3', 0)
    # 			payment(chat_id, 0, qfrom, ins3, False)
    # 			kbrd = [[InlineKeyboardButton("{p}".format(p=ticketEmoji), callback_data=templ.format(data[1], '1'))],
    # 				[InlineKeyboardButton("{p}".format(p=ticketEmoji), callback_data=templ.format(data[1], '2'))],
    # 				[InlineKeyboardButton("{e}{p}".format(e=ins3, p=coinEmoji), callback_data=templ.format(data[1], '3'))]]
    # 			if int(ins3) > 0:
    # 				sendnotif(bot, 0, qfrom, ins3, chat_id, bankcapt="ticket")
    # 		else:
    # 			return
    # 		mrkup = InlineKeyboardMarkup(kbrd)
    # 		bot.editMessageText(chat_id=query.message.chat_id, message_id=query.message.message_id, reply_markup=mrkup, text="{e} выбрал билет.".format(e=name))
    # 		async_call(async_start, args=(bot, query, name, data[1], randSave, coinEmoji, chat_id))
    # 	else:
    # 		bot.answerCallbackQuery(callback_query_id=inlmsgid, text="Это не ты платил за билеты 5{e}!".format(e=coinEmoji))
    # 		return
    # elif data[0] == 'zero':
    # 	bot.answerCallbackQuery(callback_query_id=inlmsgid, text="Ты уже открыл билет!")
    # 	return
    else:
        return


def adminpanel(bot, update, args):
    global carma, msgcount, unames, chatadmins, subscribed
    chat_id = update.message.chat_id
    from_id = update.message.from_user.id
    if from_id != botset.creatorid and from_id not in chatadmins[chat_id]:
        # bot.sendMessage(chat_id, text="Недостаточно прав", reply_to_message_id=update.message.message_id)
        return

    if len(args) == 0:
        bot.sendMessage(chat_id, text="""Available commands:
flush\nreload\nnewday\ngivecarma\nsetcarma\nmovecarma\ntakecarma""", reply_to_message_id=update.message.message_id)

    else:
        cmd = args.pop(0)
        if cmd == 'flush':
            jobhourly(None, None)
            bot.sendMessage(chat_id, text="{} done".format(cmd), reply_to_message_id=update.message.message_id)
            return
        elif cmd == "reload" and from_id == botset.creatorid:
            loaddata()
            bot.sendMessage(chat_id, text="{} done".format(cmd), reply_to_message_id=update.message.message_id)
            return
        elif cmd == 'newday':
            jobd.run(bot)
            bot.sendMessage(chat_id, text="{} done".format(cmd), reply_to_message_id=update.message.message_id)
            return
        elif cmd == 'dbgvar' and from_id == botset.creatorid:
            bot.sendMessage(chat_id, text='{}'.format(eval(' '.join(args))))
            return
        elif cmd == 'shell' and from_id == botset.creatorid:
            eval(' '.join(args))
            return
        elif cmd == 'movecarma':
            try:
                fromid = int(args[0])
                toid = int(args[1])
                amount = int(args[2])
            except:
                bot.sendMessage(chat_id, text="Usage: /admin movecarma <from_id> <to_id> <amount>")
                return
        elif cmd == 'givecarma':
            try:
                toid = int(args[0])
                amount = int(args[1])
            except:
                bot.sendMessage(chat_id, text="Usage: /admin givecarma <to_id> <amount>")
                return
            fromid = 0
        elif cmd == 'setcarma':
            try:
                toid = int(args[0])
                amount = int(args[1])
            except:
                bot.sendMessage(chat_id, text="Usage: /admin setcarma <to_id> <amount>")
                return
            carma[chat_id][toid] = amount
            return
        elif cmd == 'takecarma':
            try:
                fromid = int(args[0])
                amount = int(args[1])
            except:
                bot.sendMessage(chat_id, text="Usage: /admin takecarma <to_id> <amount>")
                return
            toid = 0
        else:
            return

        payment(chat_id, fromid, toid, amount)
        sendnotif(bot, fromid, toid, amount, chat_id, bankcapt="admin")
        bot.sendMessage(chat_id, text="{} done".format(cmd), reply_to_message_id=update.message.message_id)


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
{e}: {c}, {m}: {mc}""".format(u=getuname(uu), c=carma[chat_id].get(uid, defaultUserCarma),
                              mc=msgcount[chat_id].get(uid, 0), e=coinEmoji, m=msgEmoji)

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

    msg = get_top(chat_id, messages=False)
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

    msg = get_top(chat_id, messages=True)
    try:
        bot.sendMessage(update.message.from_user.id, text=msg)
    except:
        bot.sendMessage(update.message.chat_id, text="Невозможно отправить сообщение. Напиши в ЛС мне",
                        reply_to_message_id=update.message.message_id)


def ask(bot, update, args):
    chat_id = update.message.chat_id
    try:
        arg = int(args[0])
    except:
        # bot.sendMessage(chat_id, text="Использование: /ask <сумма>", reply_to_message_id=update.message.message_id)
        return

    toid = update.message.from_user.id
    if arg < 0:
        arg = abs(arg)
    elif arg > transferLimit:
        arg = transferLimit
    elif arg == 0:
        return

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
        if arg < 1:
            return
        if not bool(update.message.reply_to_message):
            raise ValueError
    except:
        # bot.sendMessage(chat_id, text="Использование: (в ответ на сообщение получателя) /pay <сумма>",
        # reply_to_message_id=update.message.message_id)
        return

    toid = update.message.reply_to_message.from_user.id
    if arg < 0:
        arg = abs(arg)
    elif arg > transferLimit:
        arg = transferLimit

    if toid == botid:
        toid = botset.creatorid

    if not payment(chat_id, fromid, toid, arg, True):
        bot.sendMessage(chat_id, text="Недостаточно {e}!".format(e=coinEmoji),
                        reply_to_message_id=update.message.message_id)
    else:
        bot.sendMessage(chat_id, text="{} {e} переведено.".format(arg, e=coinEmoji),
                        reply_to_message_id=update.message.message_id)
    sendnotif(bot, fromid, toid, arg, chat_id)


def thnx(bot, update):
    chat_id = update.message.chat_id
    if not bool(update.message.reply_to_message):
        # bot.sendMessage(chat_id, text="Использование: (в ответ на сообщение получателя) /thanks",
        # reply_to_message_id=update.message.message_id)
        return
    u = update.message.reply_to_message.from_user
    if u.id == update.message.from_user.id:
        # bot.sendMessage(chat_id, text="Жулик, не воруй!", reply_to_message_id=update.message.message_id)
        return
    elif u.id == botid:
        u.id = botset.creatorid
    payment(chat_id, 0, u.id, 1)
    sendnotif(bot, 0, u.id, 1, chat_id, txfrom=update.message.from_user.id)


# bot.sendMessage(chat_id, text="Добавлено +1 {e} {0}".format(getuname(u), e=coinEmoji),
# reply_to_message_id=update.message.message_id)

def feat(bot, update, args):
    chat_id = update.message.chat_id
    from_id = update.message.from_user.id
    if len(args) == 0:
        try:
            bot.sendMessage(from_id, text=features_text)
        except:
            bot.sendMessage(chat_id, text="Невозможно отправить сообщение. Напиши в ЛС мне",
                            reply_to_message_id=update.message.message_id)

    else:
        try:
            arg = int(args[0])
        except:
            arg = -1

        if arg == 1:
            if not inprivate(chat_id, from_id):
                # bot.sendMessage(chat_id, text="Здесь это делать бессмысленно",
                # reply_to_message_id=update.message.message_id)
                return
            newchat = targets.get(from_id, 0)
            if newchat == 0:
                bot.sendMessage(chat_id, text="""Чат по умолчанию не установлен.
Попроси кого-нибудь из чата выполнить команду "/start getlink" и переслать тебе.""")
                return
            args.pop(0)
            if len(args) == 0:
                bot.sendMessage(chat_id, text="Бессмысленно отправлять пустое сообщение.")
                return
            txt = ' '.join(args)
            if not payment(newchat, from_id, 0, 5, True):
                bot.sendMessage(chat_id, text="Недостаточно {e}!".format(e=coinEmoji),
                                reply_to_message_id=update.message.message_id)
                return
            bot.sendMessage(newchat, text="Сообщение от {u}:\n{m}".format(u=getuname(update.message.from_user),
                                                                          m=txt))
            bot.sendMessage(chat_id, text="Сообщение отправлено")
            sendnotif(bot, from_id, 0, 5, newchat, bankcapt="ft_1")

        elif arg == 2:
            if not inprivate(chat_id, from_id):
                # bot.sendMessage(chat_id, text="Здесь это делать бессмысленно",
                # reply_to_message_id=update.message.message_id)
                return
            newchat = targets.get(from_id, 0)
            if newchat == 0:
                bot.sendMessage(chat_id, text="""Чат по умолчанию не установлен.
Попроси кого-нибудь из чата выполнить команду "/start getlink" и переслать тебе.""")
                return
            if not payment(newchat, from_id, 0, 1, True):
                bot.sendMessage(chat_id, text="Недостаточно {e}!".format(e=coinEmoji),
                                reply_to_message_id=update.message.message_id)
                return
            bot.sendMessage(newchat, text="{u} передаёт всем привет!".format(u=getuname(update.message.from_user)))
            bot.sendMessage(chat_id, text="Сообщение отправлено")
            sendnotif(bot, from_id, 0, 1, newchat, bankcapt="ft_2")

        elif arg == 3:
            if inprivate(chat_id, from_id):
                cid = targets.get(chat_id, 0)
                if cid == 0:
                    bot.sendMessage(from_id, text="Вы не установили связь с чатом. /start для подробностей")
                    return
            else:
                cid = chat_id

            today = datetime.datetime.now()
            nohd = "Сегодня нет праздника!"
            capt = ftHolylist.get((today.day, today.month), nohd)
            amount = 10
            if capt != nohd:
                if from_id in ftHolidaygot[cid]:
                    bot.sendMessage(chat_id, text="Ты уже брал подарок!",
                                    reply_to_message_id=update.message.message_id)
                    return
                ftHolidaygot[cid].append(from_id)
                payment(cid, 0, from_id, amount)
                sendnotif(bot, 0, from_id, amount, cid, bankcapt="holiday")
            bot.sendMessage(chat_id, text=capt, reply_to_message_id=update.message.message_id)

        elif arg == 4:
            if inprivate(chat_id, from_id):
                cid = targets.get(chat_id, 0)
                if cid == 0:
                    bot.sendMessage(from_id, text="Вы не установили связь с чатом. /start для подробностей")
                    return
            else:
                cid = chat_id

            if from_id in ftStartkit[cid]:
                # bot.sendMessage(chat_id, text="Ты уже получал стартовый приз!",
                # reply_to_message_id=update.message.message_id)
                return

            ftStartkit[cid].append(from_id)
            payment(cid, 0, from_id, ftStartkitsize)
            sendnotif(bot, 0, from_id, ftStartkitsize, cid, bankcapt="ft_4")

        elif arg == 7:
            if inprivate(chat_id, from_id):
                cid = targets.get(chat_id, 0)
                if cid == 0:
                    bot.sendMessage(from_id, text="Вы не установили связь с чатом. /start для подробностей")
                    return
            else:
                cid = chat_id

            p = 5
            if from_id not in ftTestluck[cid]:
                p = 0
                ftTestluck[cid].append(from_id)

            if not payment(cid, from_id, 0, p, True):
                bot.sendMessage(chat_id, text="Недостаточно {e}!".format(e=coinEmoji),
                                reply_to_message_id=update.message.message_id)
                return
            if p != 0:
                sendnotif(bot, from_id, 0, p, cid, bankcapt="ft_7_payment")

            a = randomstuff() - p
            if a < 0:
                a = abs(a)
                bot.sendMessage(chat_id, text="Видимо, тебе не везёт. У тебя было отнято {} {e}".format(a,
                                                                                                        e=coinEmoji),
                                reply_to_message_id=update.message.message_id)
                payment(cid, from_id, 0, a)
                sendnotif(bot, from_id, 0, a, cid, bankcapt="ft_7")
            else:
                bot.sendMessage(chat_id,
                                text="Поздравляю, удача на твоей стороне! Тебе было добавлено {} {e}".format(a,
                                                                                                             e=coinEmoji),
                                reply_to_message_id=update.message.message_id)
                payment(cid, 0, from_id, a)
                sendnotif(bot, 0, from_id, a, cid, bankcapt="ft_7")

        # elif arg == 777:
        # 	chat_id_l = chat_id
        # 	if inprivate(chat_id, from_id):
        # 		chat_id = targets.get(chat_id, 0)
        # 	if not payment(chat_id, from_id, 0, 5, True):
        # 		bot.sendMessage(chat_id_l, text="Недостаточно {e}!".format(e=coinEmoji), reply_to_message_id=update.message.message_id)
        # 		return
        # 	sendnotif(bot, from_id, 0, 5, chat_id, bankcapt="777 payment")
        # 	rand_gen1 = randint(0, 10)
        # 	rand_gen2 = randint(0, 10)
        # 	rand_gen3 = randint(0, 10)
        # 	templ = 'ticket:{0}:{1}'
        # 	kbrd = [[InlineKeyboardButton("{p}".format(p=ticketEmoji), callback_data=templ.format(update.message.message_id, '1'))],
        # 		[InlineKeyboardButton("{p}".format(p=ticketEmoji), callback_data=templ.format(update.message.message_id, '2'))],
        # 		[InlineKeyboardButton("{p}".format(p=ticketEmoji), callback_data=templ.format(update.message.message_id, '3'))]]
        # 	mrkup = InlineKeyboardMarkup(kbrd)
        # 	randSave[str(chat_id) + '_' + str(update.message.message_id) + '_back'] = from_id
        # 	randSave[str(chat_id) + '_' + str(update.message.message_id) + '_name'] = getuname(update.message.from_user)
        # 	randSave[str(chat_id) + '_' + str(update.message.message_id) + '_1'] = rand_gen1
        # 	randSave[str(chat_id) + '_' + str(update.message.message_id) + '_2'] = rand_gen2
        # 	randSave[str(chat_id) + '_' + str(update.message.message_id) + '_3'] = rand_gen3
        # 	bot.sendMessage(chat_id, text="{0} выбирает билет:".format(getuname(update.message.from_user)), reply_markup=mrkup)
        else:
            try:
                bot.sendMessage(from_id, text=features_text)
            except:
                bot.sendMessage(chat_id, text="Невозможно отправить сообщение. Напиши в ЛС мне",
                                reply_to_message_id=update.message.message_id)


def statusupdate(bot, update):
    if not bool(update.message.new_chat_member):
        return
    if update.message.new_chat_member.id == botid:
        start(bot, update, ['joingroup'])


def subscr(bot, update):
    chat_id = update.message.chat_id
    from_user = update.message.from_user
    if from_user.id not in subscribed:
        try:
            bot.sendMessage(from_user.id, text='Успешно подписаны на обновления {e}'.format(e=coinEmoji))
        except:
            bot.sendMessage(chat_id, text="Невозможно подписаться на обновления. Напишите в ЛС боту",
                            reply_to_message_id=update.message.message_id)
            return
        subscribed.append(from_user.id)
    else:
        # bot.sendMessage(chat_id, text="Вы уже подписаны на обновления.", reply_to_message_id=update.message.message_id)
        return


def unsubscr(bot, update):
    chat_id = update.message.chat_id
    from_user = update.message.from_user
    if from_user.id in subscribed:
        subscribed.pop(subscribed.index(from_user.id))
        bot.sendMessage(chat_id, text="Успешно отписаны от обновлений {e}.".format(e=coinEmoji),
                        reply_to_message_id=update.message.message_id)
    else:
        bot.sendMessage(chat_id, text="Вы ещё не подписаны на обновления.",
                        reply_to_message_id=update.message.message_id)


def my_uid(bot, update):
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
    bot.sendMessage(update.message.chat_id,
                    text="Whois {}: Username: {}, FirstName: {}, LastName: {}, ChatTitle: {}".format(who.id,
                                                                                                     who.username,
                                                                                                     who.first_name,
                                                                                                     who.last_name,
                                                                                                     who.title),
                    reply_to_message_id=update.message.message_id)


def onelove(bot, update):
    m = update.message
    payment(m.chat_id, 0, m.from_user.id, 1)
    sendnotif(bot, 0, m.from_user.id, 1, m.chat_id, bankcapt="Cats4ever!")


# def gifter(bot, update, args):
# 	chat_id = update.message.chat_id
# 	chat_id_last = update.message.chat_id
# 	from_id = update.message.from_user.id
# 	if inprivate(chat_id, from_id):
# 		chat_id = targets.get(chat_id, 0)
# 		if chat_id == 0:
# 				bot.sendMessage(msg.from_user.id, text="Вы не установили связь с чатом. /start для подробностей")
# 				return
# 	if len(args) == 0:
# 		bot.sendMessage(chat_id_last, text="Использование: /gf [сумма раздачи] [по сколько выдавать]".format(e=coinEmoji), reply_to_message_id=update.message.message_id)
# 		return
# 	else:
# 		try:
# 			arg = int(args[0])
# 		except:
# 			arg = -1
# 	if arg == -1:
# 		bot.sendMessage(chat_id_last, text="Использование: /gf [сумма раздачи] [по сколько выдавать]".format(e=coinEmoji), reply_to_message_id=update.message.message_id)
# 		return
# 	if arg < 1:
# 		bot.sendMessage(chat_id_last, text="Неверная сумма {e}!".format(e=coinEmoji), reply_to_message_id=update.message.message_id)
# 		return
# 	if not payment(chat_id, from_id, 0, arg, True):
# 		bot.sendMessage(chat_id_last, text="Недостаточно {e}!".format(e=coinEmoji), reply_to_message_id=update.message.message_id)
# 	else:
# 		try:
# 			by = int(args[1])
# 		except:
# 			by = -1
# 		if (by < 1) or (by > arg):
# 			bot.sendMessage(chat_id_last, text="Неверная сумма {e}!".format(e=coinEmoji), reply_to_message_id=update.message.message_id)
# 			return
# 		giftbank[str(chat_id) + '_' + str(update.message.message_id) + '_sum'] = arg
# 		giftbank[str(chat_id) + '_' + str(update.message.message_id) + '_by'] = by
# 		giftbank[str(chat_id) + '_' + str(update.message.message_id) + '_back'] = from_id
# 		giftbank[str(chat_id) + '_' + str(update.message.message_id) + '_id'] = getuname(update.message.from_user)
# 		templ = 'gift:{}'
# 		kbrd = [[InlineKeyboardButton("Принять подарок!", callback_data=templ.format(update.message.message_id))]]
# 		mrkup = InlineKeyboardMarkup(kbrd)
# 		bot.sendMessage(chat_id, text="{0} дарит по {1}{e}. Осталось: {2}{e}".format(getuname(update.message.from_user), by, 
# 			arg, e=coinEmoji), reply_markup=mrkup)
# 		sendnotif(bot, from_id, 0, arg, chat_id, bankcapt="gifter")

updater = Updater(botset.TOKEN)
del botset.TOKEN

loaddata()

jobs = updater.job_queue
lbot = updater.bot

jobd = Job(jobdaily, 86400.0)

jobs.put(Job(jobhourly, 3600.0))
jobs.put(jobd, next_t=timediff())

botuname = lbot.getMe().username

baselink = 'telegram.me/{un}?start='.format(un=botuname)
baselink += '{}'

dp = updater.dispatcher

##########
dp.add_handler(CommandHandler('start', start, pass_args=True))
dp.add_handler(CommandHandler('help', help_))
dp.add_handler(CommandHandler('about', about))
dp.add_handler(CommandHandler('hid', hid))
dp.add_handler(CommandHandler('ping', ping))
dp.add_handler(CommandHandler('whatsnew', whatsnew))
##########
dp.add_handler(CommandHandler('uid', my_uid))
##########
dp.add_handler(CommandHandler('whois', whois, pass_args=True))
##########
dp.add_handler(CommandHandler('feature', feat, pass_args=True))
dp.add_handler(CommandHandler('ft', feat, pass_args=True))
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
dp.add_handler(RegexHandler('^\+{1,}(.+)?', thnx))
##########
dp.add_handler(CommandHandler('subscr', subscr))
dp.add_handler(CommandHandler('sub', subscr))
##########
dp.add_handler(CommandHandler('unsubscr', unsubscr))
dp.add_handler(CommandHandler('unsub', unsubscr))
##########
dp.add_handler(CommandHandler('admin', adminpanel, pass_args=True))
##########
# dp.add_handler(CommandHandler('gifter', gifter, pass_args=True))
# dp.add_handler(CommandHandler('gf', gifter, pass_args=True))
##########
dp.add_handler(RegexHandler('^Коты ван лав!$', onelove))
##########
dp.add_handler(CallbackQueryHandler(button))
dp.add_handler(MessageHandler([Filters.status_update], statusupdate))
##########
dp.add_handler(MessageHandler([], on_stuff))
##########
dp.add_error_handler(error_handler)

updater.start_polling(timeout=10, clean=True)
updater.idle()

jobhourly(None, None)
