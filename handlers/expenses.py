from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Command, Text
from datetime import datetime, date

from states.states import AddExpense, EditExpense
from database.repository import TransactionRepository
from services.pagination import pagination_service
from services.search import SearchService
from keyboards.base import get_main_keyboard, get_cancel_keyboard
from keyboards.categories import get_expense_categories_keyboard
from keyboards.pagination import get_pagination_keyboard, get_search_keyboard
from utils.validators import Validators
from utils.formatters import Formatters
from utils.exceptions import ValidationError

# Словарь для хранения состояния поиска по пользователям
user_search_states = {}

async def show_expenses_list(message: types.Message, page: int = 1, search_query: str = None):
    """Показать список расходов с пагинацией и поиском"""
    user_id = message.from_user.id
    
    # Получаем расходы с учетом поиска
    if search_query:
        # Получаем все расходы для поиска
        all_transactions, _ = await TransactionRepository.get_user_transactions(
            user_id=user_id,
            page=1,
            page_size=1000,  # Большой лимит для поиска
            trans_type='expense'
        )
        
        # Фильтруем локально
        transactions = SearchService.filter_transactions(
            [t.__dict__ for t in all_transactions],
            search_query
        )
        total = len(transactions)
        
        # Применяем пагинацию
        page_data, page_info = pagination_service.paginate_data(transactions, page)
        
    else:
        # Получаем расходы с пагинацией из БД
        transactions, total = await TransactionRepository.get_user_transactions(
            user_id=user_id,
            page=page,
            trans_type='expense'
        )
        page_info = pagination_service.get_page_info(page, total)
        page_data = transactions
    
    if not page_data:
        message_text = "📭 У вас нет расходов"
        if search_query:
            message_text += f" по запросу '{search_query}'"
        await message.answer(message_text)
        return
    
    # Формируем сообщение
    if search_query:
        message_text = f"🔍 *Результаты поиска '{search_query}':*\n\n"
    else:
        message_text = "💰 *Ваши расходы:*\n\n"
    
    for i, transaction in enumerate(page_data, 1):
        index = (page - 1) * pagination_service.page_size + i
        formatted = Formatters.format_transaction(transaction.__dict__)
        message_text += f"{index}. {formatted}\n\n"
    
    message_text += f"📄 Страница {page_info['current_page']} из {page_info['total_pages']}"
    message_text += f" (всего: {total})"
    
    # Создаем клавиатуру
    keyboard = get_pagination_keyboard(
        page_info=page_info,
        callback_prefix=f"expenses_{search_query or ''}",
        extra_buttons=[
            get_search_keyboard(search_query, "expenses_search")
        ]
    )
    
    await message.answer(message_text, parse_mode='Markdown', reply_markup=keyboard)

# Обработчики для пагинации
async def handle_expenses_page(callback_query: types.CallbackQuery):
    """Обработка перехода по страницам"""
    data = callback_query.data
    user_id = callback_query.from_user.id
    
    # Извлекаем номер страницы и поисковый запрос
    parts = data.split('_')
    page = int(parts[-1])
    
    # Получаем поисковый запрос из состояния пользователя
    search_query = user_search_states.get(user_id, {}).get('expenses', '')
    
    await callback_query.answer()
    await show_expenses_list(callback_query.message, page, search_query)

# Обработчики для поиска
async def start_expenses_search(callback_query: types.CallbackQuery, state: FSMContext):
    """Начало поиска расходов"""
    await callback_query.answer()
    
    await callback_query.message.answer(
        "🔍 Введите текст для поиска в расходах:\n\n"
        "Можно искать по категории или описанию.",
        reply_markup=get_cancel_keyboard()
    )
    
    await state.set_state("waiting_for_expenses_search")

async def process_expenses_search(message: types.Message, state: FSMContext):
    """Обработка поискового запроса"""
    if message.text == '🔙 Отмена':
        await state.finish()
        await message.answer("❌ Поиск отменен", reply_markup=get_main_keyboard())
        return
    
    search_query = message.text.strip()
    user_id = message.from_user.id
    
    # Сохраняем поисковый запрос
    if user_id not in user_search_states:
        user_search_states[user_id] = {}
    user_search_states[user_id]['expenses'] = search_query
    
    await state.finish()
    await show_expenses_list(message, page=1, search_query=search_query)

async def clear_expenses_search(callback_query: types.CallbackQuery):
    """Очистка поиска"""
    user_id = callback_query.from_user.id
    
    # Очищаем поисковый запрос
    if user_id in user_search_states:
        user_search_states[user_id].pop('expenses', None)
    
    await callback_query.answer("✅ Поиск очищен")
    await show_expenses_list(callback_query.message, page=1)

# Регистрация обработчиков
def register_expense_handlers(dp):
    """Регистрация всех обработчиков для расходов"""
    
    # Команды для отображения расходов
    dp.register_message_handler(
        lambda m: show_expenses_list(m, page=1),
        Text(equals='💰 Мои расходы')
    )
    
    # Пагинация
    dp.register_callback_query_handler(
        handle_expenses_page,
        lambda c: c.data.startswith('expenses_page_')
    )
    
    # Поиск
    dp.register_callback_query_handler(
        start_expenses_search,
        lambda c: c.data == 'expenses_search_start'
    )
    
    dp.register_message_handler(
        process_expenses_search,
        state="waiting_for_expenses_search"
    )
    
    dp.register_callback_query_handler(
        clear_expenses_search,
        lambda c: c.data == 'expenses_search_clear'
    )
    
    # Остальные обработчики (добавление, редактирование и т.д.)
    # ... (аналогично оригиналу, но с использованием репозиториев и валидаторов)