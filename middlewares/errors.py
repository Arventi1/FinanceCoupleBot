from aiogram import types
from aiogram.dispatcher.middlewares import BaseMiddleware
from aiogram.dispatcher.handler import CancelHandler
import logging

from utils.exceptions import (
    FinanceBotError, ValidationError, DatabaseError, 
    NotFoundError, AuthError, PaginationError
)

logger = logging.getLogger(__name__)

class ErrorMiddleware(BaseMiddleware):
    """Middleware для обработки ошибок"""
    
    async def on_process_message(self, message: types.Message, data: dict):
        """Обработка ошибок для сообщений"""
        try:
            return await super().on_process_message(message, data)
        except Exception as e:
            await self._handle_error(e, message)
            raise CancelHandler()
    
    async def on_process_callback_query(self, callback_query: types.CallbackQuery, data: dict):
        """Обработка ошибок для callback-запросов"""
        try:
            return await super().on_process_callback_query(callback_query, data)
        except Exception as e:
            await self._handle_error(e, callback_query.message, callback_query)
            raise CancelHandler()
    
    async def _handle_error(self, error: Exception, message: types.Message = None, 
                           callback_query: types.CallbackQuery = None):
        """Обработка различных типов ошибок"""
        target = message or (callback_query.message if callback_query else None)
        
        if not target:
            logger.error(f"Ошибка без контекста: {error}")
            return
        
        error_message = self._get_error_message(error)
        
        try:
            await target.answer(error_message)
        except Exception as e:
            logger.error(f"Не удалось отправить сообщение об ошибке: {e}")
        
        # Логируем ошибку
        user_info = f"Пользователь: {callback_query.from_user.id if callback_query else message.from_user.id}"
        logger.error(f"{user_info} | Ошибка: {error.__class__.__name__}: {error}")
    
    def _get_error_message(self, error: Exception) -> str:
        """Получить понятное сообщение об ошибке"""
        if isinstance(error, ValidationError):
            return f"❌ Ошибка ввода: {str(error)}"
        elif isinstance(error, DatabaseError):
            if config.DEBUG:
                return f"❌ Ошибка базы данных: {str(error)}"
            else:
                return "❌ Произошла ошибка при работе с базой данных. Попробуйте позже."
        elif isinstance(error, NotFoundError):
            return f"❌ {str(error)}"
        elif isinstance(error, AuthError):
            return "❌ Ошибка авторизации. Доступ запрещен."
        elif isinstance(error, PaginationError):
            return f"❌ Ошибка пагинации: {str(error)}"
        elif isinstance(error, FinanceBotError):
            return f"❌ Ошибка: {str(error)}"
        else:
            if config.DEBUG:
                return f"❌ Неизвестная ошибка: {str(error)}"
            else:
                return "❌ Произошла неизвестная ошибка. Попробуйте позже."