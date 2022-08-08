from application import telegram_bot
from config import Config
from application.core import userservice, orderservice
from application.resources import strings, keyboards
from application.utils import bot as botutils
from flask import Blueprint, request, abort
import telebot
import os
import settings as stngs

bp = Blueprint('bot', __name__)

from application.bot import registration, catalog, cart, comments, my_orders, settings, notifications, about, search

if 'PRODUCTION' in os.environ:
    @bp.route(Config.WEBHOOK_URL_PATH, methods=['POST'])
    def receive_message():
        if request.headers.get('content-type') == 'application/json':
            try:
                json_string = request.get_data().decode('utf-8')
                update = telebot.types.Update.de_json(json_string)
                telegram_bot.process_new_updates([update])
            finally:
                return ''
        else:
            abort(400)
    if 'TEST' in os.environ:
        telegram_bot.polling()
    else:
        telegram_bot.remove_webhook()
        telegram_bot.set_webhook(Config.WEBHOOK_URL_BASE + Config.WEBHOOK_URL_PATH)


def check_contacts(message: telebot.types.Message):
    if not message.text:
        return False
    user_id = message.from_user.id
    user = userservice.get_user_by_telegram_id(user_id)
    if not user:
        return False
    language = user.language
    return strings.get_string('main_menu.contacts', language) in message.text and 'private' in message.chat.type


@telegram_bot.message_handler(commands=['/contacts'])
@telegram_bot.message_handler(content_types='text', func=lambda m: botutils.check_auth(m) and check_contacts(m))
def contacts(message: telebot.types.Message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    language = userservice.get_user_language(user_id)

    contacts = stngs.get_contacts()
    telegram_bot.send_message(chat_id, strings.from_contacts(contacts, language))


@telegram_bot.message_handler(content_types=['text'], func=lambda m: m.chat.type == 'private')
def empty_message(message: telebot.types.Message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    if not userservice.is_user_registered(user_id):
        registration.welcome(message)
        return
    language = userservice.get_user_language(user_id)
    main_menu_message = strings.get_string('main_menu.choose_option', language)
    main_menu_keyboard = keyboards.get_keyboard('main_menu', language)
    telegram_bot.send_message(chat_id, main_menu_message, reply_markup=main_menu_keyboard)
    return
