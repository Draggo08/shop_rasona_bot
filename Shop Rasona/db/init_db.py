import aiosqlite

async def init_db():
    async with aiosqlite.connect('shop_rasona.db') as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                registration_date TEXT,
                last_topup_date TEXT,
                balance INTEGER,
                num_purchased_items INTEGER
            )
        ''')

        await db.execute('''
            CREATE TABLE IF NOT EXISTS products (
                product_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                price INTEGER
            )
        ''')

        await db.commit()

if __name__ == "__main__":
    import asyncio
    asyncio.run(init_db())