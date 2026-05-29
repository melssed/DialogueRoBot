from aiogram import Bot, Dispatcher, Router
from aiogram.filters import CommandStart
from aiogram.types import Message
import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID"))

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
router = Router()

@router.message(CommandStart())
async def start(message: Message):
    if message.from_user.id != OWNER_ID:
        return
    await message.answer(
        "🕵️ *Spy Bot активен!*\n\n"
        "Я слежу за твоими чатами и уведомлю о:\n"
        "✏️ Изменении сообщений\n"
        "🗑 Удалении сообщений\n"
        "⏳ Медиа с таймером",
        parse_mode="Markdown"
    )

dp.include_router(router)