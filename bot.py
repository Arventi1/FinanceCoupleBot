import asyncio
import logging
import sys
import traceback
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.utils import executor
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# Импортируем конфиг ПЕРВЫМ, чтобы проверить переменные окружения
from config import config

# --- Настройка логирования ---
def setup_logging():
    """Настройка системы логирования"""
    # Формат логов
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # Уровень логирования в зависимости от DEBUG
    log_level = logging.DEBUG if config.DEBUG else logging.INFO
    
    # Настройка корневого логгера
    logging.basicConfig(
        level=log_level,
        format=log_format,
        handlers=[
            # Вывод в консоль
            logging.StreamHandler(sys.stdout),
            # Запись в файл
            logging.FileHandler(config.LOG_FILE, encoding='utf-8')
        ]
    )
    
    # Устанавливаем уровень для aiogram (чтобы не было слишком много логов)
    logging.getLogger('aiogram').setLevel(logging.WARNING if config.DEBUG else logging.ERROR)
    
    logger = logging.getLogger(__name__)
    logger.info("✅ Система логирования инициализирована")
    
    return logger

# Инициализируем логирование сразу
logger = setup_logging()

# --- Инициализация бота ---
try:
    bot = Bot(token=config.BOT_TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(bot, storage=storage)
    
    logger.info("✅ Бот инициализирован")
except Exception as e:
    logger.error(f"❌ Ошибка инициализации бота: {e}")
    sys.exit(1)

# --- Планировщик задач ---
scheduler = AsyncIOScheduler(timezone="UTC")

# --- Импорт модулей ---
try:
    from database.connection import db_connection
    from database.models import CREATE_TABLES_SQL, CREATE_INDEXES_SQL
    from middlewares.auth import AuthMiddleware
    from middlewares.errors import ErrorMiddleware
    from services.notifications import NotificationService
    
    logger.info("✅ Модули успешно импортированы")
except ImportError as e:
    logger.error(f"❌ Ошибка импорта модулей: {e}")
    logger.error("Проверьте, что все файлы присутствуют в проекте")
    sys.exit(1)

# --- Инициализация базы данных ---
async def init_database():
    """Инициализация базы данных"""
    try:
        logger.info("🔄 Инициализация базы данных...")
        
        # Инициализируем подключение
        await db_connection.initialize()
        
        # Создаем таблицы
        async with db_connection.get_connection() as db:
            for i, sql in enumerate(CREATE_TABLES_SQL, 1):
                try:
                    await db.execute(sql)
                    logger.debug(f"  Создана таблица {i}/{len(CREATE_TABLES_SQL)}")
                except Exception as e:
                    logger.warning(f"  Предупреждение при создании таблицы {i}: {e}")
            
            # Создаем индексы
            for i, sql in enumerate(CREATE_INDEXES_SQL, 1):
                try:
                    await db.execute(sql)
                    logger.debug(f"  Создан индекс {i}/{len(CREATE_INDEXES_SQL)}")
                except Exception as e:
                    logger.warning(f"  Предупреждение при создании индекса {i}: {e}")
            
            await db.commit()
        
        logger.info("✅ База данных инициализирована")
        
    except Exception as e:
        logger.error(f"❌ Ошибка инициализации БД: {e}")
        logger.error(traceback.format_exc())
        raise

# --- Регистрация обработчиков ---
def register_handlers():
    """Регистрация всех обработчиков"""
    try:
        # Импортируем здесь, чтобы избежать циклических импортов
        from handlers.base import register_base_handlers
        from handlers.expenses import register_expense_handlers
        from handlers.incomes import register_income_handlers
        from handlers.plans import register_plan_handlers
        from handlers.purchases import register_purchase_handlers
        from handlers.statistics import register_statistics_handlers
        from handlers.management import register_management_handlers
        from handlers.shared import register_shared_handlers
        
        # Регистрируем базовые обработчики
        register_base_handlers(dp)
        
        # Регистрируем обработчики расходов
        register_expense_handlers(dp)
        
        # Регистрируем обработчики доходов
        register_income_handlers(dp)
        
        # Регистрируем обработчики планов
        register_plan_handlers(dp)
        
        # Регистрируем обработчики покупок
        register_purchase_handlers(dp)
        
        # Регистрируем обработчики статистики
        register_statistics_handlers(dp)
        
        # Регистрируем обработчики управления
        register_management_handlers(dp)
        
        # Регистрируем обработчики общих финансов
        register_shared_handlers(dp)
        
        logger.info("✅ Обработчики зарегистрированы")
        
    except Exception as e:
        logger.error(f"❌ Ошибка регистрации обработчиков: {e}")
        logger.error(traceback.format_exc())
        raise

# --- Функция для обработки неожиданных ошибок ---
def handle_exception(exc_type, exc_value, exc_traceback):
    """Обработчик необработанных исключений"""
    if issubclass(exc_type, KeyboardInterrupt):
        # Не логируем KeyboardInterrupt
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    
    logger.critical("❌ НЕОБРАБОТАННОЕ ИСКЛЮЧЕНИЕ", exc_info=(exc_type, exc_value, exc_traceback))

# Устанавливаем обработчик исключений
sys.excepthook = handle_exception

# --- Обработчики запуска и остановки ---
async def on_startup(dispatcher: Dispatcher):
    """Действия при запуске бота"""
    try:
        logger.info("=" * 50)
        logger.info("🚀 Запуск бота...")
        logger.info("=" * 50)
        
        # Инициализация БД
        await init_database()
        
        # Регистрация middleware
        dp.middleware.setup(AuthMiddleware())
        dp.middleware.setup(ErrorMiddleware())
        
        logger.info("✅ Middleware зарегистрированы")
        
        # Регистрация обработчиков
        register_handlers()
        
        # Запуск планировщика уведомлений
        try:
            notification_service = NotificationService(bot)
            await notification_service.schedule_all()
            logger.info("✅ Планировщик уведомлений запущен")
        except Exception as e:
            logger.warning(f"⚠️  Не удалось запустить планировщик уведомлений: {e}")
        
        # Отправляем уведомление владельцу
        if config.ALLOWED_USERS:
            for user_id in config.ALLOWED_USERS[:1]:  # Только первому пользователю
                try:
                    await bot.send_message(
                        user_id,
                        "🤖 Бот успешно запущен и готов к работе!\n\n"
                        "Используйте /start для начала работы."
                    )
                    logger.info(f"✅ Уведомление отправлено пользователю {user_id}")
                    break
                except Exception as e:
                    logger.warning(f"⚠️  Не удалось отправить уведомление пользователю {user_id}: {e}")
        
        logger.info("✅ Бот успешно запущен и готов к работе!")
        logger.info("=" * 50)
        
    except Exception as e:
        logger.error(f"❌ Критическая ошибка при запуске бота: {e}")
        logger.error(traceback.format_exc())
        raise

async def on_shutdown(dispatcher: Dispatcher):
    """Действия при остановке бота"""
    try:
        logger.info("=" * 50)
        logger.info("🛑 Остановка бота...")
        
        # Останавливаем планировщик
        if scheduler.running:
            scheduler.shutdown(wait=False)
            logger.info("✅ Планировщик остановлен")
        
        # Закрываем подключение к БД
        await db_connection.close()
        logger.info("✅ Подключение к БД закрыто")
        
        # Отправляем уведомление владельцу
        if config.ALLOWED_USERS:
            for user_id in config.ALLOWED_USERS[:1]:  # Только первому пользователю
                try:
                    await bot.send_message(user_id, "🤖 Бот остановлен. До скорой встречи! 👋")
                except:
                    pass
        
        logger.info("✅ Бот успешно остановлен")
        logger.info("=" * 50)
        
    except Exception as e:
        logger.error(f"❌ Ошибка при остановке бота: {e}")

# --- Основная функция ---
def main():
    """Точка входа в приложение"""
    try:
        logger.info("🤖 Запуск бота 'Финансы для двоих'...")
        
        # Запускаем бота
        executor.start_polling(
            dp,
            skip_updates=True,  # Пропускаем сообщения, пока бот был offline
            on_startup=on_startup,
            on_shutdown=on_shutdown,
            timeout=30,  # Таймаут для запросов
            relax=0.1,   # Задержка между запросами
            fast=True    # Быстрый режим обработки
        )
        
    except KeyboardInterrupt:
        logger.info("⏹️  Бот остановлен пользователем (Ctrl+C)")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка в работе бота: {e}")
        logger.error(traceback.format_exc())
        sys.exit(1)

# Точка входа
if __name__ == '__main__':
    main()