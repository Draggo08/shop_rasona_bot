import aiosqlite
from datetime import datetime

class User:
    @classmethod
    async def get(cls, user_id):
        async with aiosqlite.connect('shop_rasona.db') as db:
            async with db.execute('SELECT * FROM users WHERE user_id = ?', (user_id,)) as cursor:
                user = await cursor.fetchone()
                if user:
                    return {
                        'user_id': user[0],
                        'username': user[1],
                        'registration_date': user[2],
                        'last_topup_date': user[3],
                        'balance': user[4],
                        'num_purchased_items': user[5]
                    }
                return None

    @classmethod
    async def create(cls, user_id, username):
        registration_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        async with aiosqlite.connect('shop_rasona.db') as db:
            await db.execute('''
                INSERT INTO users (user_id, username, registration_date, last_topup_date, balance, num_purchased_items) ```python
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, username, registration_date, registration_date, 0, 0))
            await db.commit()
        return await cls.get(user_id)

    @classmethod
    async def update_balance(cls, user_id, new_balance):
        async with aiosqlite.connect('shop_rasona.db') as db:
            await db.execute('UPDATE users SET balance = ? WHERE user_id = ?', (new_balance, user_id))
            await db.commit()

    @classmethod
    async def update_user(cls, user_id, last_topup_date=None, new_balance=None, num_purchased_items=None):
        async with aiosqlite.connect('shop_rasona.db') as db:
            user = await cls.get(user_id)
            if not user:
                return
            if last_topup_date:
                user['last_topup_date'] = last_topup_date
            if new_balance is not None:
                user['balance'] = new_balance
            if num_purchased_items is not None:
                user['num_purchased_items'] += num_purchased_items

            await db.execute('''
                UPDATE users SET 
                    last_topup_date = ?, 
                    balance = ?, 
                    num_purchased_items = ? 
                WHERE user_id = ?''',
                (user['last_topup_date'], user['balance'], user['num_purchased_items'], user_id))
            await db.commit()

class Product:
    @classmethod
    async def get_all(cls):
        async with aiosqlite.connect('shop_rasona.db') as db:
            async with db.execute('SELECT * FROM products') as cursor:
                products = await cursor.fetchall()
                return [
                    {
                        'product_id': row[0],
                        'name': row[1],
                        'price': row[2]
                    } for row in products
                ]

    @classmethod
    async def get(cls, product_id):
        async with aiosqlite.connect('shop_rasona.db') as db:
            async with db.execute('SELECT * FROM products WHERE product_id = ?', (product_id,)) as cursor:
                product = await cursor.fetchone()
                if product:
                    return {
                        'product_id': product[0],
                        'name': product[1],
                        'price': product[2]
                    }
                return None

    @classmethod
    async def create(cls, name, price):
        async with aiosqlite.connect('shop_rasona.db') as db:
            await db.execute('''
                INSERT INTO products (name, price)
                VALUES (?, ?)
            ''', (name, price))
            await db.commit()

    @classmethod
    async def update(cls, product_id, name=None, price=None):
        async with aiosqlite.connect('shop_rasona.db') as db:
            product = await cls.get(product_id)
            if not product:
                return
            if name is not None:
                product['name'] = name
            if price is not None:
                product['price'] = price

            await db.execute('''
                UPDATE products SET name = ?, price = ? WHERE product_id = ?
            ''', (product['name'], product['price'], product_id))
            await db.commit()

    @classmethod
    async def delete(cls, product_id):
        async with aiosqlite.connect('shop_rasona.db') as db:
            await db.execute('DELETE FROM products WHERE product_id = ?', (product_id,))
            await db.commit()