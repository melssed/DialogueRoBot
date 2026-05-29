import asyncio
from aiogram import Bot, Dispatcher
from bot import bot, dp
import userbot
from database import init_db

async def main():
    await init_db()
    print("✅ БД подключена!")
    
    userbot._bot = bot
    print("✅ Бот передан в юзербот!")
    
    async def run_userbot():
        await userbot.app.start()
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