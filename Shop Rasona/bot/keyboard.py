from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_main_menu():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    buttons = [
        KeyboardButton('Личный кабинет'),
        KeyboardButton('Пополнение баланса'),
        KeyboardButton('Баланс'),
        KeyboardButton('Каталог')
    ]
    keyboard.add(*buttons)
    return keyboard