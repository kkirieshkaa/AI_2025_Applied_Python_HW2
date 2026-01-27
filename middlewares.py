from aiogram import BaseMiddleware
from aiogram.types import Message

from db import get_user

class LoggingMiddleware(BaseMiddleware):
    async def __call__(self, handler, event: Message, data: dict):
        text = event.text or ""
        if text.startswith("/"):
            print(f"Получена команда: {text}")
        return await handler(event, data)
    

class UserMiddleware(BaseMiddleware):
    async def __call__(self, handler, event: Message, data: dict):
        user = get_user(event.from_user.id)
        data["user"] = user
        data["p"] = user["profile"]
        data["d"] = user["daily"]
        return await handler(event, data)