import aiosqlite

DB_PATH = "messages.db"

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                chat_id INTEGER,
                message_id INTEGER,
                text TEXT,
                file_id TEXT,
                file_type TEXT,
                date INTEGER,
                PRIMARY KEY (chat_id, message_id)
            )
        """)
        await db.commit()

async def save_message(chat_id, message_id, text, file_id=None, file_type=None, date=0):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT OR REPLACE INTO messages 
            (chat_id, message_id, text, file_id, file_type, date)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (chat_id, message_id, text or "", file_id, file_type, date))
        await db.commit()

async def get_message(chat_id, message_id):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT text, file_id, file_type FROM messages WHERE chat_id=? AND message_id=?",
            (chat_id, message_id)
        ) as cursor:
            return await cursor.fetchone()

async def delete_message(chat_id, message_id):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "DELETE FROM messages WHERE chat_id=? AND message_id=?",
            (chat_id, message_id)
        )
        await db.commit()