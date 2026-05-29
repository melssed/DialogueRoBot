import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message
import os
from dotenv import load_dotenv
from database import save_message, get_message, delete_message

load_dotenv()

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
OWNER_ID = int(os.getenv("OWNER_ID"))
SESSION_STRING = os.getenv("SESSION_STRING")

_bot = None

def set_bot(bot):
    global _bot
    _bot = bot

app = Client(
    "userbot",
    api_id=API_ID,
    api_hash=API_HASH,
    session_string=SESSION_STRING
)

def get_file_info(message: Message):
    if message.photo:
        return message.photo.file_id, "photo"
    elif message.video:
        return message.video.file_id, "video"
    elif message.voice:
        return message.voice.file_id, "voice"
    elif message.video_note:
        return message.video_note.file_id, "video_note"
    elif message.document:
        return message.document.file_id, "document"
    elif message.audio:
        return message.audio.file_id, "audio"
    return None, None

@app.on_message(filters.private & ~filters.me)
async def on_new_message(client, message: Message):
    try:
        file_id, file_type = get_file_info(message)
        
        if message.media and getattr(message, 'ttl_seconds', None):
            await handle_timed_media(client, message)
            return
        
        await save_message(
            chat_id=message.chat.id,
            message_id=message.id,
            text=message.text or message.caption or "",
            file_id=file_id,
            file_type=file_type,
            date=int(message.date.timestamp()) if message.date else 0
        )
        print(f"💾 Сохранено сообщение {message.id} от {message.chat.id}")
    except Exception as e:
        print(f"❌ Ошибка сохранения: {e}")

async def handle_timed_media(client, message: Message):
    if not _bot:
        return
    chat = message.chat
    sender_name = getattr(chat, 'first_name', '') or getattr(chat, 'title', 'Unknown')
    username = f"@{chat.username}" if getattr(chat, 'username', None) else f"ID: {chat.id}"
    caption = f"⏳ *Медиа с таймером!*\nОт: {sender_name} ({username})"
    try:
        file_path = await client.download_media(message)
        if message.photo:
            await _bot.send_photo(OWNER_ID, file_path, caption=caption)
        elif message.video or message.video_note:
            await _bot.send_video(OWNER_ID, file_path, caption=caption)
        elif message.voice:
            await _bot.send_voice(OWNER_ID, file_path, caption=caption)
        else:
            await _bot.send_document(OWNER_ID, file_path, caption=caption)
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
    except Exception as e:
        await _bot.send_message(OWNER_ID, f"⏳ Медиа с таймером от {sender_name}, ошибка: {e}")

@app.on_edited_message(filters.private & ~filters.me)
async def on_edited_message(client, message: Message):
    if not _bot:
        return
    try:
        old_data = await get_message(message.chat.id, message.id)
        chat = message.chat
        sender_name = getattr(chat, 'first_name', '') or getattr(chat, 'title', 'Unknown')
        username = f"@{chat.username}" if getattr(chat, 'username', None) else f"ID: {chat.id}"
        old_text = old_data['text'] if old_data else "*(неизвестно)*"
        new_text = message.text or message.caption or "*(медиа)*"
        notification = (
            f"✏️ *Сообщение изменено!*\n"
            f"От: {sender_name} ({username})\n\n"
            f"*Было:*\n{old_text}\n\n"
            f"*Стало:*\n{new_text}"
        )
        await _bot.send_message(OWNER_ID, notification, parse_mode="Markdown")
        file_id, file_type = get_file_info(message)
        await save_message(message.chat.id, message.id, new_text, file_id, file_type)
    except Exception as e:
        print(f"❌ Ошибка изменения: {e}")

@app.on_deleted_messages(filters.private)
async def on_deleted_message(client, messages):
    if not _bot:
        return
    for message in messages:
        try:
            old_data = await get_message(message.chat.id, message.id)
            if not old_data:
                await _bot.send_message(
                    OWNER_ID,
                    f"🗑 *Сообщение удалено!*\nChat ID: `{message.chat.id}`\n_(текст не сохранён)_",
                    parse_mode="Markdown"
                )
                continue
            old_text = old_data['text']
            file_id = old_data['file_id']
            file_type = old_data['file_type']
            notification = f"🗑 *Сообщение удалено!*\n\n*Текст:*\n{old_text}" if old_text else "🗑 *Сообщение удалено!*"
            if file_id and file_type:
                try:
                    if file_type == "photo":
                        await _bot.send_photo(OWNER_ID, file_id, caption=notification)
                    elif file_type in ("video", "video_note"):
                        await _bot.send_video(OWNER_ID, file_id, caption=notification)
                    elif file_type == "voice":
                        await _bot.send_voice(OWNER_ID, file_id, caption=notification)
                    else:
                        await _bot.send_document(OWNER_ID, file_id, caption=notification)
                except Exception:
                    await _bot.send_message(OWNER_ID, notification, parse_mode="Markdown")
            else:
                await _bot.send_message(OWNER_ID, notification, parse_mode="Markdown")
            await delete_message(message.chat.id, message.id)
        except Exception as e:
            print(f"❌ Ошибка удаления: {e}")