from application import telegram_bot as bot
from application.core import dishservice, userservice
from application.resources import strings, keyboards
from application.utils import bot as botutils
from telebot.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from . import cart as user_cart
from time import sleep

def check_search(message: Message):
    if not message.text:
        return False
    user_id = message.from_user.id
    user = userservice.get_user_by_telegram_id(user_id)
    if not user:
        return False
    language = user.language
    return strings.get_string('main_menu.search', language) in message.text and 'private' in message.chat.type


@bot.message_handler(commands=['/search'])
@bot.message_handler(content_types='text', func=lambda m: botutils.check_auth(m) and check_search(m))
def search(message: Message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    language = userservice.get_user_language(user_id)
    message = strings.get_string('search.input', language)
    keyboard = keyboards.get_keyboard('go_back', language)
    bot.send_message(chat_id, message, reply_markup=keyboard)
    bot.register_next_step_handler_by_chat_id(chat_id, search_processor)


@bot.callback_query_handler(func=lambda call: str(call.data).startswith('dish_cart:'))
def show_count_keyboard_query(call):
    chat_id = call.message.chat.id
    user_id = call.from_user.id
    language = userservice.get_user_language(user_id)
    bot.answer_callback_query(call.id)
    dish_id = int(call.data[len('dish_cart:'):])
    keyboard = InlineKeyboardMarkup(row_width=3)
    keyboard.add(*[InlineKeyboardButton(bytes([0x30 + number, 0xef, 0xb8, 0x8f, 0xe2, 0x83, 0xa3]).decode(),
        callback_data='dish_add:' + str(dish_id) + ':' + str(number)) for number in list(range(1, 10))])
    bot.edit_message_reply_markup(chat_id, message_id=call.message.message_id, reply_markup=keyboard)


@bot.callback_query_handler(func=lambda call: str(call.data).startswith('dish_add:'))
def add_to_cart_query(call):
    chat_id = call.message.chat.id
    user_id = call.from_user.id
    language = userservice.get_user_language(user_id)
    bot.answer_callback_query(call.id, text=strings.get_string('cart.added', language), show_alert=True)

    segments = str(call.data).split(':')
    dish_id = segments[1]
    count = segments[2]
    dish = dishservice.get_dish_by_id(dish_id)
    userservice.add_dish_to_cart(user_id, dish, count)
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton(strings.get_string('search.to_cart', language), callback_data='cart'))
    bot.edit_message_reply_markup(chat_id, message_id=call.message.message_id, reply_markup=keyboard)


@bot.callback_query_handler(func=lambda call: str(call.data) == 'cart')
def go_to_cart_query(call):
    bot.answer_callback_query(call.id)
    user_cart.cart_processor(call.message)


def search_processor(message: Message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    language = userservice.get_user_language(user_id)

    def error():
        message = strings.get_string('search.error', language)
        bot.send_message(chat_id, message)
        bot.register_next_step_handler_by_chat_id(chat_id, search_processor)

    if not message.text or len(message.text) < 2:
        error()
        return
    if strings.get_string('go_back', language) in message.text:
        botutils.to_main_menu(chat_id, language)
        return
    
    terms = message.text
    dishes = dishservice.search(terms, language)

    bot.send_message(chat_id, strings.get_string('search.results'), reply_markup=keyboards.get_keyboard('main_menu'))

    for dish in dishes:
        dish_info = strings.from_dish(dish, language)
        dish_keyboard = InlineKeyboardMarkup()
        dish_keyboard.add(InlineKeyboardButton(strings.get_string('cart.add'), callback_data='dish_cart:' + str(dish.id)))
        if dish.image_path:
            try:
                image = open(dish.image_path, 'rb')
            except FileNotFoundError:
                bot.send_message(chat_id, dish_info, reply_markup=dish_keyboard)
            else:
                bot.send_photo(chat_id, image, caption=dish_info, reply_markup=dish_keyboard)
        else:
            bot.send_message(chat_id, dish_info, reply_markup=dish_keyboard)
        sleep(1 / 10)
