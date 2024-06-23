import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from bot.handlers import setup_handlers
from bot.settings import BOT_TOKEN

async def main():
    bot = Bot(token=BOT_TOKEN)
    storage = MemoryStorage()  # Добавлено хранилище состояний в память
    dp = Dispatcher(bot, storage=storage)

    setup_handlers(dp)

    await dp.start_polling()

if __name__ == "__main__":
    asyncio.run(main())