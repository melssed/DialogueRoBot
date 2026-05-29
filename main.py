import asyncio
from aiogram import Bot, Dispatcher
from bot import bot, dp
from userbot import app, set_bot
from database import init_db
import os

async def main():
    # Инициализируем БД
    await init_db()
    
    # Передаём bot в userbot для отправки уведомлений
    set_bot(bot)
    
    print("✅ Запуск бота и юзербота...")
    
    # Запускаем оба параллельно
    await asyncio.gather(
        app.start(),
        dp.start_polling(bot)
    )

if __name__ == "__main__":
    asyncio.run(main())
