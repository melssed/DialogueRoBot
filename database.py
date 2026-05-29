import os
import asyncpg

_pool = None

async def init_db():
    global _pool
    database_url = os.getenv("DATABASE_URL")
    _pool = await asyncpg.create_pool(database_url)
    await _pool.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            chat_id BIGINT,
            message_id BIGINT,
            text TEXT,
            file_id TEXT,
            file_type TEXT,
            date BIGINT,
            PRIMARY KEY (chat_id, message_id)
        )
    """)

async def save_message(chat_id, message_id, text, file_id=None, file_type=None, date=0):
    await _pool.execute("""
        INSERT INTO messages (chat_id, message_id, text, file_id, file_type, date)
        VALUES ($1, $2, $3, $4, $5, $6)
        ON CONFLICT (chat_id, message_id) DO UPDATE
        SET text=$3, file_id=$4, file_type=$5, date=$6
    """, chat_id, message_id, text or "", file_id, file_type, date)

async def get_message(chat_id, message_id):
    row = await _pool.fetchrow(
        "SELECT text, file_id, file_type FROM messages WHERE chat_id=$1 AND message_id=$2",
        chat_id, message_id
    )
    return row

async def delete_message(chat_id, message_id):
    await _pool.execute(
        "DELETE FROM messages WHERE chat_id=$1 AND message_id=$2",
        chat_id, message_id
    )