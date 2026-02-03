from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Command
import logging

from keyboards.base import get_main_keyboard
from utils.exceptions import AuthError

logger = logging.getLogger(__name__)

async def cmd_start(message: types.Message):
    """Обработчик команды /start"""
    try:
        welcome_text = f"""
👋 Привет, {message.from_user.first_name}!

Я твой личный финансовый помощник и планировщик для двоих!

📌 **Основные возможности:**
• 💰 Учет расходов и доходов
• 📊 Статистика и аналитика
• 👥 Общие финансы и сравнение
• 📅 Планировщик с напоминаниями
• 🛒 Список желаемых покупок
• 🔍 Поиск и фильтрация записей
• 📄 Пагинация для удобного просмотра

🆕 **Новые функции:**
• ✏️ Редактирование записей
• 🗑️ Удаление с подтверждением
• 🔙 Отмена любого действия
• 👥 Общие планы

Используй кнопки ниже!
"""
        
        await message.answer(welcome_text, reply_markup=get_main_keyboard())
        logger.info(f"Пользователь {message.from_user.id} запустил бота")
        
    except Exception as e:
        logger.error(f"Ошибка в команде /start: {e}")
        await message.answer("❌ Произошла ошибка. Попробуйте позже.")

async def cmd_help(message: types.Message):
    """Обработчик команды /help"""
    help_text = """
📚 **Справка по командам:**

/start - Запустить бота
/help - Показать эту справку
/cancel - Отменить текущее действие

📱 **Основные функции:**
• Используйте кнопки меню для навигации
• Все действия можно отменить кнопкой "🔙 Отмена"
• Для поиска используйте 🔍 в списках

💡 **Советы:**
• Регулярно добавляйте расходы
• Планируйте крупные покупки заранее
• Используйте статистику для анализа

🆘 **Поддержка:**
Если возникли проблемы, обратитесь к администратору.
"""
    
    await message.answer(help_text, parse_mode='Markdown')

async def cmd_cancel(message: types.Message, state: FSMContext):
    """Отмена любого действия"""
    current_state = await state.get_state()
    
    if current_state is None:
        await message.answer("✅ Нет активных действий для отмены", reply_markup=get_main_keyboard())
        return
    
    await state.finish()
    await message.answer("❌ Действие отменено", reply_markup=get_main_keyboard())
    logger.info(f"Пользователь {message.from_user.id} отменил действие в состоянии {current_state}")

async def handle_unknown(message: types.Message):
    """Обработчик неизвестных команд"""
    await message.answer(
        "🤔 Я не понял эту команду.\n\n"
        "Используйте /start для начала работы или /help для справки.",
        reply_markup=get_main_keyboard()
    )

def register_base_handlers(dp):
    """Регистрация базовых обработчиков"""
    dp.register_message_handler(cmd_start, commands=['start'])
    dp.register_message_handler(cmd_help, commands=['help'])
    dp.register_message_handler(cmd_cancel, commands=['cancel'], state='*')
    dp.register_message_handler(cmd_cancel, Text(equals='🔙 Отмена'), state='*')
    dp.register_message_handler(handle_unknown)