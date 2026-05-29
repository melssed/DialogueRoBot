import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.enums import MessageMediaType
import os
from dotenv import load_dotenv
from database import save_message, get_message, delete_message

load_dotenv()

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
OWNER_ID = int(os.getenv("OWNER_ID"))

# Глобальная ссылка на bot для отправки уведомлений
_bot = None

def set_bot(bot):
    global _bot
    _bot = bot

app = Client("userbot_session", api_id=API_ID, api_hash=API_HASH)

def get_file_info(message: Message):
    """Получить file_id и тип медиа из сообщения"""
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
    elif message.sticker:
        return message.sticker.file_id, "sticker"
    return None, None

@app.on_message(filters.private & ~filters.me)
async def on_new_message(client, message: Message):
    """Сохраняем все входящие сообщения в БД"""
    file_id, file_type = get_file_info(message)
    
    # Обрабатываем медиа с таймером (once-view)
    if message.media and hasattr(message, 'ttl_seconds') and message.ttl_seconds:
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

async def handle_timed_media(client, message: Message):
    """Скачиваем медиа с таймером и пересылаем владельцу"""
    if not _bot:
        return
    
    chat = message.chat
    sender_name = getattr(chat, 'first_name', '') or getattr(chat, 'title', 'Unknown')
    username = f"@{chat.username}" if getattr(chat, 'username', None) else f"ID: {chat.id}"
    
    caption = (
        f"⏳ *Медиа с таймером!*\n"
        f"От: {sender_name} ({username})"
    )
    
    try:
        # Скачиваем файл через userbot
        file_path = await client.download_media(message)
        
        # Определяем тип и отправляем через бота
        if message.photo or (message.media and 'photo' in str(message.media)):
            await _bot.send_photo(OWNER_ID, file_path, caption=caption)
        elif message.video or message.video_note:
            await _bot.send_video(OWNER_ID, file_path, caption=caption)
        elif message.voice:
            await _bot.send_voice(OWNER_ID, file_path, caption=caption)
        else:
            await _bot.send_document(OWNER_ID, file_path, caption=caption)
            
        # Удаляем временный файл
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
    except Exception as e:
        await _bot.send_message(OWNER_ID, f"⏳ Медиа с таймером от {sender_name}, но не удалось скачать: {e}")

@app.on_edited_message(filters.private & ~filters.me)
async def on_edited_message(client, message: Message):
    """Уведомление об изменении сообщения"""
    if not _bot:
        return
    
    old_data = await get_message(message.chat.id, message.id)
    
    chat = message.chat
    sender_name = getattr(chat, 'first_name', '') or getattr(chat, 'title', 'Unknown')
    username = f"@{chat.username}" if getattr(chat, 'username', None) else f"ID: {chat.id}"
    
    old_text = old_data[0] if old_data else "*(неизвестно)*"
    new_text = message.text or message.caption or "*(медиа)*"
    
    notification = (
        f"✏️ *Сообщение изменено!*\n"
        f"От: {sender_name} ({username})\n\n"
        f"*Было:*\n{old_text}\n\n"
        f"*Стало:*\n{new_text}"
    )
    
    await _bot.send_message(OWNER_ID, notification, parse_mode="Markdown")
    
    # Обновляем в БД
    file_id, file_type = get_file_info(message)
    await save_message(message.chat.id, message.id, new_text, file_id, file_type)

@app.on_deleted_messages(filters.private)
async def on_deleted_message(client, messages):
    """Уведомление об удалении сообщения"""
    if not _bot:
        return
    
    for message in messages:
        old_data = await get_message(message.chat.id, message.id)
        
        if not old_data:
            continue
        
        old_text, file_id, file_type = old_data
        
        notification = f"🗑 *Сообщение удалено!*\nChat ID: {message.chat.id}\n\n"
        
        if old_text:
            notification += f"*Текст:*\n{old_text}"
        
        # Если было медиа — пересылаем файл
        if file_id and file_type:
            try:
                if file_type == "photo":
                    await _bot.send_photo(OWNER_ID, file_id, caption=notification)
                elif file_type in ("video", "video_note"):
                    await _bot.send_video(OWNER_ID, file_id, caption=notification)
                elif file_type == "voice":
                    await _bot.send_voice(OWNER_ID, file_id, caption=notification)
                elif file_type == "document":
                    await _bot.send_document(OWNER_ID, file_id, caption=notification)
                else:
                    await _bot.send_message(OWNER_ID, notification, parse_mode="Markdown")
            except Exception:
                await _bot.send_message(OWNER_ID, notification, parse_mode="Markdown")
        else:
            await _bot.send_message(OWNER_ID, notification, parse_mode="Markdown")
        
        await delete_message(message.chat.id, message.id)