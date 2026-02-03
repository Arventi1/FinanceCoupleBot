from aiogram import types
from aiogram.dispatcher.middlewares import BaseMiddleware
from aiogram.dispatcher.handler import CancelHandler
import logging

from config import config
from database.repository import UserRepository

logger = logging.getLogger(__name__)

class AuthMiddleware(BaseMiddleware):
    """Middleware для проверки авторизации"""
    
    async def on_pre_process_message(self, message: types.Message, data: dict):
        """Проверка авторизации для сообщений"""
        await self._check_user(message.from_user)
    
    async def on_pre_process_callback_query(self, callback_query: types.CallbackQuery, data: dict):
        """Проверка авторизации для callback-запросов"""
        await self._check_user(callback_query.from_user)
    
    async def _check_user(self, user: types.User):
        """Проверка пользователя"""
        user_id = user.id
        
        # Проверяем, есть ли пользователь в списке разрешенных
        if user_id not in config.ALLOWED_USERS:
            logger.warning(f"Попытка доступа от неавторизованного пользователя: {user_id}")
            raise CancelHandler()
        
        # Регистрируем пользователя в БД
        try:
            await UserRepository.create_or_update(
                user_id=user_id,
                username=user.username,
                full_name=user.full_name or f"{user.first_name or ''} {user.last_name or ''}".strip()
            )
        except Exception as e:
            logger.error(f"Ошибка регистрации пользователя {user_id}: {e}")
            # Не блокируем пользователя при ошибке БД
            pass