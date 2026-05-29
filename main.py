import asyncio
from aiogram import Bot, Dispatcher
from bot import bot, dp
from userbot import app, set_bot
from database import init_db
import os

async def main():
    await init_db()
    set_bot(bot)
    print("✅ Запуск бота и юзербота...")
    
    async def run_userbot():
        await app.start()
        print("✅ Юзербот запущен!")
        await asyncio.Event().wait()

    async def run_bot():
        print("✅ Бот запущен!")
        await dp.start_polling(bot)

    await asyncio.gather(
        run_userbot(),
        run_bot()
    )

if __name__ == "__main__":
    asyncio.run(main())