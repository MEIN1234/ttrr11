# -*- coding: utf-8 -*-
import os
from background import keep_alive #импорт функции для поддержки работоспособности
import pip
pip.main(['install', 'pytelegrambotapi'])
import requests
import telebot
from telebot import types
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
# import requests # Удалены неиспользуемые импорты
# import time     # Удалены неиспользуемые импорты

# --- Константы ---
TOKEN = '8321838627:AAE3S9czdKbG1mJG0rDW9KrFT7i31UB1sg0'
ADMIN_CHAT_ID = 6055009734    # Ваш Telegram ID
# Удалены дублирующиеся переменные ADMIN_ID и API_TOKEN

# --- Создание экземпляра бота (Один раз!) ---
bot = telebot.TeleBot(TOKEN)

# Каталог товаров: категория -> название товара -> цена
catalog = {
    '✨ drugs': {
        'Heroine, for 1g': 70,
        'Methadone, for 1g': 40,
        'Tramadol, for 100g': 80,
        'Mephedrone, for 1g': 20,
        'Marijuana,for 10g': 60,
        'Ecstasy, for 20pieces': 155,
        'LSD,for 2pieces': 25,
        'MDMA, for 1g': 33,
        'Mushrooms psycho, for 10g': 55
    },
    '🔫 guns': {
        'M16,army model': 870,
        'Ak-47, Russian army model': 500,
        'Beretta ARX160': 500,
        'AR-15': 900
    },
}

# Корзина пользователей: user_id -> [(название, цена), ...]
user_cart = {}

@bot.message_handler(commands=['start', 'menu'])
def send_welcome(message):
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    for category in catalog.keys():
        markup.add(types.KeyboardButton(category))
    markup.add(types.KeyboardButton('cart'))
    markup.add(types.KeyboardButton('pay'))
bot.send_message(
    message.chat.id, 
    f"""Hello, {message.from_user.first_name}! 
    On our marketplace you can buy: best guns, drugs and soon documents for all anything✨✨✨ 
    All of this is imported from Mexico,Russia,Ukraine,Portugal and locally produced 👨‍🌾"f"
    Choose category:""",
    reply_markup=markup
)

@bot.message_handler(func=lambda message: message.text in catalog.keys())
def show_products(message):
    category = message.text
    markup = types.InlineKeyboardMarkup()
    for product, price in catalog[category].items():
        markup.add(types.InlineKeyboardButton(
            text=f'{product} - {price}$',
            callback_data=f"add|{category}|{product}"
        ))
    markup.add(types.InlineKeyboardButton("◀Back", callback_data="back_to_menu"))
    bot.send_message(
        message.chat.id,
        f"Category: {category}. Choose product:",
        reply_markup=markup
    )

@bot.message_handler(func=lambda message: message.text == 'cart')
def show_cart(message):
    user_id = message.from_user.id
    cart = user_cart.get(user_id, [])
    if not cart:
        bot.send_message(user_id, "Your cart empty.")
        return
    text = "Your cart:\n"
    total = 0
    for i, (product, price) in enumerate(cart, 1):
        text += f"{i}. {product} — {price}$\n"
        total += price
    text += f"\nTotal: {total}$" # Изменил "Итого" на "Total" для унификации
    bot.send_message(user_id, text)

@bot.message_handler(func=lambda message: message.text == 'pay')
def payment_start(message):
    user_id = message.from_user.id
    cart = user_cart.get(user_id, [])
    if not cart:
        bot.send_message(user_id, "Your cart empty. Choose product.")
        return
    markup = InlineKeyboardMarkup()
    pay_button = InlineKeyboardButton("pay", callback_data="pay")
    markup.add(pay_button)
    bot.send_message(user_id, "Press button, to send a payment request. After payments, use /area <text> to indicate district where we will leave goods",
                     reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('add|'))
def add_to_cart(call):
    _, category, product = call.data.split('|')
    price = catalog[category][product]
    user_id = call.from_user.id
    user_cart.setdefault(user_id, []).append((product, price))

    bot.answer_callback_query(call.id, f"add to cart: {product} — {price}$")

@bot.callback_query_handler(func=lambda call: call.data == 'back_to_menu')
def back_to_menu(call):
    bot.delete_message(call.message.chat.id, call.message.message_id)
    send_welcome(call.message)


@bot.callback_query_handler(func=lambda call: call.data == "pay")
def callback_pay(call):
    user = call.from_user
    # Внимание: здесь русский комментарий, лучше его удалить или заменить
    username = user.username if user.username else "no username"
    user_id = user.id
    cart = user_cart.get(user_id, [])
    if not cart:
        bot.answer_callback_query(call.id, "Your cart empty.")
        return

    total = sum(price for _, price in cart)
    try:
        # Внимание: здесь русские слова "Новая заявка", "Содержимое корзины", "Общая сумма"
        # Для сервера лучше использовать английский, или убедиться, что кодировка работает
        bot.send_message(
            ADMIN_CHAT_ID,
            f"New payment request from @{username} (ID: {user_id}).\n"
            f"Cart contents:\n" +
            "\n".join([f"- {product} — {price}$" for product, price in cart]) +
            f"\n\nTotal amount: {total}$\n"
            f"To send requisites, use command:\n"
            f"/send_requisites {user_id} <requisites text>"
        )
        bot.answer_callback_query(call.id, "Application has been sent to administrator. You will be contacted soon")
        user_cart[user_id] = []  # Очистить корзину после отправки заявки
    except Exception as e:
        bot.answer_callback_query(call.id, "error when sending.")
        print(f"Error in callback_pay: {e}")

@bot.message_handler(commands=['area'])
def send_to_admin(message):
    text = message.text.replace('/area ', '', 1).strip()
    if text:
        username = message.from_user.username or message.from_user.first_name
        user_id = message.from_user.id
        msg = f"Message from @{username} (id {user_id}):\n{text}" # Изменил на английский
        bot.send_message(ADMIN_CHAT_ID, msg)
        bot.reply_to(message, "Your message sent to administrator.")
    else:
        bot.reply_to(message, "Enter text after command /area.")


@bot.message_handler(commands=['send_requisites'])
def send_requisites(message):
    if message.chat.id != ADMIN_CHAT_ID:
        bot.reply_to(message, "Access is denied")
        return
    parts = message.text.split(maxsplit=2)
    if len(parts) < 3:
        bot.reply_to(message, "Usage: /send_requisites <user_id> <requisites>") # Изменил на английский
        return
    user_id_str = parts[1]
    requisites_text = parts[2]
    try:
        user_id = int(user_id_str)
    except ValueError:
        bot.reply_to(message, "Error: user_id must be a number.") # Изменил на английский
        return
    try:
        bot.send_message(user_id, f"Hello! payment details:\n{requisites_text}")
        bot.reply_to(message, f"Requisites sent to user {user_id}") # Изменил на английский
    except Exception as e:
        bot.reply_to(message, f"Error sending to user: {e}") # Изменил на английский


if __name__ == '__main__':
    keep_alive()  # Запуск веб-сервера Flask в отдельном потоке
    print("Бот запущен!")
    bot.infinity_polling()
