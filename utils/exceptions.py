class FinanceBotError(Exception):
    """Базовое исключение для бота"""
    pass

class DatabaseError(FinanceBotError):
    """Ошибка базы данных"""
    pass

class ValidationError(FinanceBotError):
    """Ошибка валидации"""
    pass

class AuthError(FinanceBotError):
    """Ошибка авторизации"""
    pass

class NotFoundError(FinanceBotError):
    """Объект не найден"""
    pass

class PaginationError(FinanceBotError):
    """Ошибка пагинации"""
    pass