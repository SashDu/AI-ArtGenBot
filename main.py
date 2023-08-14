from uuid import uuid4
import os
import openai
import requests
import telebot
from io import BytesIO
from telebot import types
from dotenv import load_dotenv

load_dotenv()
openai.api_key = os.getenv('MY_API_KEY')
bot = telebot.TeleBot(os.getenv('BOT_KEY'))
user_input = {}


def download_from_link(url: str):
    response = requests.get(url)
    return response.content


def make_prompt(base: str, styles: str, description: str):
    prompt = f'{base} {styles} {description}'
    return prompt


@bot.message_handler(commands=['start'])
def handle_start(message):
    user_input[message.chat.id] = {}
    bot.send_message(message.chat.id, 'Введите ваш запрос')
    bot.register_next_step_handler(message, process_base)


def process_base(message):
    chat_id = message.chat.id
    if chat_id not in user_input:
        user_input[chat_id] = {}

    base = message.text.strip()
    if not base:
        bot.send_message(chat_id, 'Ошибка: Ваш запрос не может быть пустым')
        return
    elif base.isdigit():
        bot.send_message(chat_id, 'Ошибка: Ваш запрос не может содержать цифры')
        return
    elif base.isspace():
        bot.send_message(chat_id, 'Ошибка: Ваш запрос не может состоять из пробелов')
        return

    for char in base:
        if char.isdigit():
            bot.send_message(chat_id, 'Ошибка: Вы не можете вводить цифры')
            return

    user_input[chat_id]['base'] = base

    bot.send_message(chat_id, 'Здесь можно описать стиль или пропустить(-)')
    bot.register_next_step_handler(message, process_styles)


def process_styles(message):
    chat_id = message.chat.id
    styles = message.text.strip()
    user_input[chat_id]['styles'] = styles

    bot.send_message(chat_id, 'Можно дополнить ваш запрос дополнительной информацией или пропустить(-)')
    bot.register_next_step_handler(message, process_description)


def process_description(message):
    chat_id = message.chat.id
    description = message.text.strip()
    user_input[chat_id]['description'] = description

    base = user_input[chat_id]['base']
    styles = user_input[chat_id]['styles']
    description = user_input[chat_id]['description']

    prompt = make_prompt(base, styles, description)

    response = openai.Image.create(
        prompt=prompt,
        n=3,
        size='1024x1024'
    )
    images = []
    for i, data in enumerate(response['data']):
        image_data = download_from_link(url=data['url'])
        photo_stream = BytesIO(image_data)
        photo_stream.seek(0)
        images.append(photo_stream)

    for image in images:
        bot.send_photo(chat_id=message.chat.id, photo=image)

    user_input.pop(chat_id)


@bot.message_handler(commands=['stop'])
def handle_stop(message):
    bot.send_message(message.chat.id, 'Работа бота прекращена')
    bot.stop_polling()


bot.set_my_commands([
    types.BotCommand('/start', 'Запустить процесс'),
    types.BotCommand('/stop', 'Остановить бота')
])

bot.polling()