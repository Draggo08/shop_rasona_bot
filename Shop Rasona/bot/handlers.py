from aiogram import types, Dispatcher
from aiogram.dispatcher.filters import Text
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from datetime import datetime

from bot.keyboard import get_main_menu
from bot.settings import CHANNELS
from utils.checker import is_subscribed
from utils.payments import create_payment_link, check_payment
from db.models import User, Product

class PaymentState(StatesGroup):
    amount = State()


async def start_cmd(message: types.Message):
    user_id = message.from_user.id
    if not await is_subscribed(user_id):
        await message.answer(
            "Перед началом работы, пожалуйста, подпишитесь на каналы: {} и {}".format(CHANNELS[0], CHANNELS[1]),
            reply_markup=ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton('Проверить подписку'))
        )
    else:
        await message.answer('Добро пожаловать!', reply_markup=get_main_menu())


async def check_subscription(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.username
    if await is_subscribed(user_id):
        user = await User.get(user_id)
        if not user:
            user = await User.create(user_id, username)
        await personal_account(message)
    else:
        await message.answer('Пожалуйста, подпишитесь на каналы {} и {}'.format(CHANNELS[0], CHANNELS[1]))


async def personal_account(message: types.Message):
    user_id = message.from_user.id
    user = await User.get(user_id)
    if user:
        registration_date = user["registration_date"]
        username = user["username"]
        last_topup_date = user["last_topup_date"]
        balance = user["balance"]
        num_purchased_items = user["num_purchased_items"]
        await message.answer(
            f"""Личный кабинет\n\n
Дата регистрации: {registration_date}\n
Юзернейм: {username}\n
Дата последнего пополнения: {last_topup_date}\n
Количество купленных товаров: {num_purchased_items}"""
        )
    else:
        username = message.from_user.username
        new_user = await User.create(user_id, username)
        await message.answer('Ваш аккаунт был создан. Пожалуйста, используйте команду снова.')


async def balance(message: types.Message):
    user_id = message.from_user.id
    user = await User.get(user_id)
    if user:
        await message.answer(f'Ваш баланс: {user["balance"]} токенов')
    else:
        await message.answer('Аккаунт не найден.')


async def catalog(message: types.Message):
    products = await Product.get_all()
    if products:
        for product in products:
            await message.answer(
                f'{product["name"]} - {product["price"]} токенов',
                reply_markup=InlineKeyboardMarkup().add(
                    InlineKeyboardButton('Купить', callback_data=f'buy_{product["product_id"]}')
                )
            )
    else:
        await message.answer("В магазине пока нет товаров.")


async def payment(message: types.Message):
    await PaymentState.amount.set()
    await message.answer('Введите количество токенов, которые вы хотите приобрести:')


async def process_amount(message: types.Message, state: FSMContext):
    try:
        amount = int(message.text)
        if amount <= 0:
            await message.answer('Пожалуйста, введите положительное количество токенов.')
            return

        async with state.proxy() as data:
            data['amount'] = amount

        user_id = message.from_user.id
        try:
            payment_link = await create_payment_link(user_id, amount)
            await message.answer(
                f'Перейдите по следующей ссылке для пополнения баланса: {payment_link}',
                reply_markup=ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton('Проверить оплату'))
            )
        except Exception as e:
            await message.answer(f'Произошла ошибка при создании платежной ссылки: {str(e)}')

        await state.finish()
    except ValueError:
        await message.answer('Пожалуйста, введите целое число токенов.')


async def check_payment_status(message: types.Message):
    user_id = message.from_user.id
    if await check_payment(user_id):
        user = await User.get(user_id)
        async with state.proxy() as data:
            amount = data.get('amount', 0)
        await User.update_balance(user_id, user['balance'] + amount)
        await message.answer('Ваш баланс успешно пополнен.', reply_markup=get_main_menu())
    else:
        await message.answer('Оплата не найдена. Пожалуйста, попробуйте снова.')


async def process_buy(callback_query: types.CallbackQuery):
    product_id = callback_query.data.split('_')[1]
    product = await Product.get(product_id)

    if not product:
        await callback_query.message.answer(f'Товар с ID {product_id} не найден.')
        return

    user_id = callback_query.from_user.id
    user = await User.get(user_id)

    if user['balance'] >= product['price']:
        new_balance = user['balance'] - product['price']
        await User.update_user(user_id, new_balance=new_balance, num_purchased_items=1)
        await callback_query.message.answer(
            f'Вы купили {product["name"]} за {product["price"]} токенов!\n'
            f'Ваш новый баланс: {new_balance} токенов.\n'
            'Пожалуйста, отправьте скриншот в личные сообщения для подтверждения покупки.'
        )
    else:
        await callback_query.message.answer('У вас недостаточно токенов для покупки данного товара.')

class AddProductState(StatesGroup):
    name = State()
    price = State()

class DeleteProductState(StatesGroup):
    id = State()

class UpdateProductState(StatesGroup):
    id = State()
    name = State()
    price = State()

async def admin_panel(message: types.Message):
    admin_buttons = [
        KeyboardButton('Добавить товар'),
        KeyboardButton('Удалить товар'),
        KeyboardButton('Изменить товар'),
        KeyboardButton('Просмотреть все товары')
    ]
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(*admin_buttons)
    await message.answer('Добро пожаловать в администрирование магазина', reply_markup=keyboard)

async def add_product(message: types.Message):
    await message.answer('Введите название товара:')
    await AddProductState.name.set()

async def add_product_handler(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['name'] = message.text
    await AddProductState.next()
    await message.answer("Теперь введите цену товара:")

async def add_product_handler_price(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['price'] = int(message.text)
    await Product.create(data['name'], data['price'])
    await message.answer(f"Товар '{data['name']}' с ценой {data['price']} добавлен в магазин")
    await state.finish()

async def view_products(message: types.Message):
    products = await Product.get_all()
    if products:
        reply = '\n'.join([f"{product['product_id']}: {product['name']} - {product['price']} токенов" for product in products])
        await message.answer(f"Список всех товаров:\n{reply}")
    else:
        await message.answer("В магазине пока нет товаров.")

async def delete_product(message: types.Message):
    await message.answer('Введите ID товара, который хотите удалить:')
    await DeleteProductState.id.set()

async def delete_product_handler(message: types.Message, state: FSMContext):
    product_id = int(message.text)
    await Product.delete(product_id)
    await message.answer(f"Товар с ID {product_id} был удален.")
    await state.finish()

async def update_product(message: types.Message):
    await message.answer('Введите ID товара, который хотите изменить:')
    await UpdateProductState.id.set()

async def update_product_handler(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['id'] = int(message.text)
    await UpdateProductState.next()
    await message.answer("Введите новое название товара:")

async def update_product_handler_name(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['name'] = message.text
    await UpdateProductState.next()
    await message.answer("Введите новую цену товара:")

async def update_product_handler_price(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['price'] = int(message.text)
    await Product.update(data['id'], data['name'], data['price'])
    await message.answer(f"Товар '{data['name']}' был обновлен с новой ценой {data['price']}.")
    await state.finish()

def setup_handlers(dp: Dispatcher):
    dp.register_message_handler(start_cmd, commands='start')
    dp.register_message_handler(check_subscription, Text(equals='Проверить подписку'))
    dp.register_message_handler(personal_account, Text(equals='Личный кабинет'))
    dp.register_message_handler(balance, Text(equals='Баланс'))
    dp.register_message_handler(catalog, Text(equals='Каталог'))
    dp.register_message_handler(payment, Text(equals='Пополнение баланса'))
    dp.register_message_handler(process_amount, state=PaymentState.amount)
    dp.register_message_handler(check_payment_status, Text(equals='Проверить оплату'))
    dp.register_callback_query_handler(process_buy, lambda c: c.data.startswith('buy_'))
    dp.register_message_handler(admin_panel, commands=['admin'])
    dp.register_message_handler(add_product, Text(equals='Добавить товар'))
    dp.register_message_handler(delete_product, Text(equals='Удалить товар'))
    dp.register_message_handler(update_product, Text(equals='Изменить товар'))
    dp.register_message_handler(view_products, Text(equals='Просмотреть все товары'))
    dp.register_message_handler(add_product_handler, state=AddProductState.name)
    dp.register_message_handler(add_product_handler_price, state=AddProductState.price)
    dp.register_message_handler(delete_product_handler, state=DeleteProductState.id)
    dp.register_message_handler(update_product_handler, state=UpdateProductState.id)
    dp.register_message_handler(update_product_handler_name, state=UpdateProductState.name)
    dp.register_message_handler(update_product_handler_price, state=UpdateProductState.price)
