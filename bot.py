import asyncio

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from config import TOKEN
from handlers import setup_handlers
from middlewares import LoggingMiddleware, UserMiddleware


bot = Bot(token=TOKEN)

dp = Dispatcher(storage=MemoryStorage())

dp.message.middleware(LoggingMiddleware())
dp.message.middleware(UserMiddleware())
setup_handlers(dp)


async def main():
    print("Бот запущен!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
