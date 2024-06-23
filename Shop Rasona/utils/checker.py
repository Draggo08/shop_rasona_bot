import aiohttp
from bot.settings import BOT_TOKEN, CHANNELS

async def is_subscribed(user_id):
    async with aiohttp.ClientSession() as session:
        for channel in CHANNELS:
            async with session.get(f'https://api.telegram.org/bot{BOT_TOKEN}/getChatMember?chat_id={channel}&user_id={user_id}') as response:
                result = await response.json()
                if 'result' not in result:
                    return False
                if result['result']['status'] not in ['member', 'administrator', 'creator']:
                    return False
    return True