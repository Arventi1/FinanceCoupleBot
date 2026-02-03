import os
import sys
from typing import List

class Config:
    def __init__(self):
        # Проверяем обязательные переменные
        self._check_required_vars()
        
        # Базовые настройки
        self.BOT_TOKEN = os.getenv('BOT_TOKEN')
        
        # Получаем список разрешенных пользователей
        allowed_users_str = os.getenv('ALLOWED_USERS', '')
        
        if allowed_users_str:
            # Парсим из строки: "123,456,789"
            self.ALLOWED_USERS = []
            for user_id in allowed_users_str.split(','):
                try:
                    self.ALLOWED_USERS.append(int(user_id.strip()))
                except ValueError:
                    print(f"⚠️  Предупреждение: Неверный ID пользователя '{user_id}' пропущен")
        else:
            # Старая схема для обратной совместимости
            self.ALLOWED_USERS = []
            my_id = os.getenv('MY_USER_ID')
            gf_id = os.getenv('GIRLFRIEND_USER_ID')
            
            if my_id:
                try:
                    self.ALLOWED_USERS.append(int(my_id))
                except ValueError:
                    print(f"⚠️  Предупреждение: Неверный MY_USER_ID '{my_id}'")
            
            if gf_id:
                try:
                    self.ALLOWED_USERS.append(int(gf_id))
                except ValueError:
                    print(f"⚠️  Предупреждение: Неверный GIRLFRIEND_USER_ID '{gf_id}'")
        
        # Проверяем, есть ли разрешенные пользователи
        if not self.ALLOWED_USERS:
            print("⚠️  ВНИМАНИЕ: Не указаны разрешенные пользователи! Используйте ALLOWED_USERS или MY_USER_ID/GIRLFRIEND_USER_ID")
        
        # Остальные настройки
        self.DB_PATH = os.getenv('DB_PATH', 'finance_planner.db')
        self.DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
        
        # Пагинация
        self.PAGE_SIZE = int(os.getenv('PAGE_SIZE', '5'))
        self.MAX_PAGE_SIZE = int(os.getenv('MAX_PAGE_SIZE', '10'))
        
        # Ограничения
        self.MAX_DESCRIPTION_LENGTH = int(os.getenv('MAX_DESCRIPTION_LENGTH', '500'))
        self.MAX_TITLE_LENGTH = int(os.getenv('MAX_TITLE_LENGTH', '100'))
        self.MAX_CATEGORY_LENGTH = int(os.getenv('MAX_CATEGORY_LENGTH', '50'))
        
        # Путь для логов
        self.LOG_FILE = os.getenv('LOG_FILE', 'bot.log')
        
        # Вывод информации о конфигурации
        self._print_config_info()
    
    def _check_required_vars(self):
        """Проверка обязательных переменных окружения"""
        required_vars = ['BOT_TOKEN']
        missing_vars = []
        
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            print("❌ КРИТИЧЕСКАЯ ОШИБКА: Отсутствуют обязательные переменные окружения!")
            for var in missing_vars:
                print(f"   - {var}")
            print("\n📋 Укажите их в настройках хостинга:")
            print("   BOT_TOKEN=ваш_токен_от_BotFather")
            print("   ALLOWED_USERS=123456789,987654321")
            print("\n💡 Или используйте старый формат:")
            print("   MY_USER_ID=123456789")
            print("   GIRLFRIEND_USER_ID=987654321")
            sys.exit(1)
    
    def _print_config_info(self):
        """Вывод информации о конфигурации"""
        print("=" * 50)
        print("🤖 Конфигурация бота загружена:")
        print("=" * 50)
        
        # Маскируем токен для безопасности
        token_display = self.BOT_TOKEN
        if token_display and len(token_display) > 8:
            token_display = token_display[:4] + "..." + token_display[-4:]
        
        print(f"📱 BOT_TOKEN: {token_display}")
        print(f"👥 ALLOWED_USERS: {self.ALLOWED_USERS}")
        print(f"💾 DB_PATH: {self.DB_PATH}")
        print(f"🐛 DEBUG: {self.DEBUG}")
        print(f"📄 PAGE_SIZE: {self.PAGE_SIZE}")
        print(f"📝 LOG_FILE: {self.LOG_FILE}")
        print("=" * 50)
    
    def is_user_allowed(self, user_id: int) -> bool:
        """Проверка, разрешен ли пользователь"""
        # Если список пустой - разрешаем всем (для тестирования)
        if not self.ALLOWED_USERS:
            print(f"⚠️  ВНИМАНИЕ: Пользователь {user_id} получил доступ, так как ALLOWED_USERS не задан")
            return True
        
        return user_id in self.ALLOWED_USERS

# Глобальный экземпляр конфигурации
config = Config()