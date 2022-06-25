from application import telegram_bot
from application.core import userservice
from application.resources import strings, keyboards
from application.utils import bot as botutils
from telebot.types import Message
import re

### SETTINGS

def check_settings(message: Message):
    if not message.text:
        return False
    user_id = message.from_user.id
    user = userservice.get_user_by_telegram_id(user_id)
    if not user:
        return False
    language = user.language
    return strings.get_string('main_menu.settings', language) in message.text and message.chat.type == 'private'


@telegram_bot.message_handler(commands=['settings'])
@telegram_bot.message_handler(content_types=['text'], func=lambda m: botutils.check_auth(m) and check_settings(m))
def settings_handler(message: Message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    language = userservice.get_user_language(user_id)

    settings_message = strings.get_string('main_menu.choose_option', language)
    settings_keyboard = keyboards.get_keyboard('settings_menu', language)
    telegram_bot.send_message(chat_id, settings_message, reply_markup=settings_keyboard, parse_mode='HTML')
    telegram_bot.register_next_step_handler_by_chat_id(chat_id, settings_processor)


def settings_processor(message: Message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    language = userservice.get_user_language(user_id)

    if strings.get_string('main_menu.language', language) in message.text:
        language_handler(message)
    elif strings.get_string('main_menu.phone', language) in message.text:
        phone_handler(message)
    elif strings.get_string('go_back', language) in message.text:
        botutils.to_main_menu(chat_id, language)
    else:
        settings_handler(message)


### LANGUAGE

def language_handler(message: Message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    language = userservice.get_user_language(user_id)

    change_language_message = strings.get_string('language.change', language)
    change_language_keyboard = keyboards.from_change_language(language)
    telegram_bot.send_message(chat_id, change_language_message, reply_markup=change_language_keyboard, parse_mode='HTML')
    telegram_bot.register_next_step_handler_by_chat_id(chat_id, change_language_processor)


def change_language_processor(message: Message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    language = userservice.get_user_language(user_id)

    def error():
        error_msg = strings.get_string('language.change', language)
        telegram_bot.send_message(chat_id, error_msg)
        telegram_bot.register_next_step_handler_by_chat_id(chat_id, change_language_processor)

    if not message.text:
        error()
        return
    if strings.get_string('go_back', language) in message.text:
        botutils.to_main_menu(chat_id, language)
        return
    elif strings.get_string('language.russian') in message.text:
        new_language = 'ru'
        userservice.set_user_language(user_id, new_language)
    elif strings.get_string('language.uzbek') in message.text:
        new_language = 'uz'
    else:
        error()
        return
    userservice.set_user_language(user_id, new_language)
    success_message = strings.get_string('language.success', new_language)
    botutils.to_main_menu(chat_id, new_language, success_message)


def phone_handler(message: Message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    language = userservice.get_user_language(user_id)

    change_phone_message = strings.get_string('phone.change', language)
    change_phone_keyboard = keyboards.from_user_phone_number(language, go_back=True)
    telegram_bot.send_message(chat_id, change_phone_message, reply_markup=change_phone_keyboard, parse_mode='HTML')
    telegram_bot.register_next_step_handler_by_chat_id(chat_id, change_phone_processor)


def change_phone_processor(message: Message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    language = userservice.get_user_language(user_id)

    def error():
        error_msg = strings.get_string('phone.change', language)
        telegram_bot.send_message(chat_id, error_msg)
        telegram_bot.register_next_step_handler_by_chat_id(chat_id, change_phone_processor)

    if message.contact is not None:
        phone_number = message.contact.phone_number
    else:
        if message.text is None:
            error()
            return
        elif strings.get_string('go_back', language) in message.text:
            botutils.to_main_menu(chat_id, language)
            return
        else:
            match = re.match(r'\+*998\s*\d{2}\s*\d{3}\s*\d{2}\s*\d{2}', message.text)
            if match is None:
                error()
                return
            phone_number = match.group()

    userservice.set_user_phone_number(user_id, phone_number)
    success_message = strings.get_string('phone.success', language)
    botutils.to_main_menu(chat_id, language, success_message)
