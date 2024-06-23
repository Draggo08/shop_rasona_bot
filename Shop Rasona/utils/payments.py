import aiohttp
from bot.settings import YOO_MONEY_TOKEN
YOOMONEY_PAYMENT_PAGE_URL = "https://yoomoney.ru/to/4100118715025637"  # Ваша ссылка на страницу оплаты


async def create_payment_link(user_id, amount):
    # На данном этапе просто формируем URL для перенаправления на страницу оплаты
    payment_link = f"{YOOMONEY_PAYMENT_PAGE_URL}?sum={amount}&target=Заказ%20{user_id}&formcomment=Пополнение%20баланса"
    return payment_link


async def check_payment(user_id):
    # Так как мы не можем проверить оплату напрямую (от ЮMoney), дополнительно нужно проверить у себя в системе
    # Используем метод вручную внесения идентификатора операции и проверки через ЮMoney API

    # Пример кода для ручной проверки, чтобы показать принципы
    async with aiohttp.ClientSession() as session:
        headers = {
            "Authorization": f"Bearer {YOO_MONEY_TOKEN}",
        }
        params = {
            "label": user_id  # Используйте label или другие дополнительные параметры для поиска
        }
        async with session.get(f"https://yoomoney.ru/api/operation-history", params=params,
                               headers=headers) as response:
            result = await response.json()
            if "operations" in result:
                for operation in result["operations"]:
                    if operation["label"] == user_id and operation["status"] == "success":
                        return True
    return False