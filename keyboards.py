from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

def get_main_keyboard():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    keyboard.add(
        KeyboardButton('💰 Добавить расход'),
        KeyboardButton('💵 Добавить доход')
    )
    keyboard.add(
        KeyboardButton('📊 Статистика'),
        KeyboardButton('👫 Общие финансы')
    )
    keyboard.add(
        KeyboardButton('📅 Добавить план'),
        KeyboardButton('🛒 Добавить покупку')
    )
    keyboard.add(
        KeyboardButton('📝 Мои планы'),
        KeyboardButton('📋 Мои покупки')
    )
    return keyboard

def get_expense_categories_keyboard():
    """Категории для расходов"""
    keyboard = InlineKeyboardMarkup(row_width=2)
    categories = ['Еда', 'Транспорт', 'Развлечения', 'Одежда', 'Жилье', 'Здоровье', 'Подарки', 'Другое']
    buttons = [InlineKeyboardButton(cat, callback_data=f'expense_cat_{cat}') for cat in categories]
    keyboard.add(*buttons)
    return keyboard

def get_income_categories_keyboard():
    """Категории для доходов"""
    keyboard = InlineKeyboardMarkup(row_width=2)
    categories = ['Зарплата', 'Подработка', 'Инвестиции', 'Подарок', 'Возврат долга', 'Прочее']
    buttons = [InlineKeyboardButton(cat, callback_data=f'income_cat_{cat}') for cat in categories]
    keyboard.add(*buttons)
    return keyboard

def get_statistics_menu_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton('📊 Моя статистика', callback_data='stats_my'),
        InlineKeyboardButton('👫 Общая статистика', callback_data='stats_combined')
    )
    keyboard.add(
        InlineKeyboardButton('👤 Статистика партнера', callback_data='stats_partner'),
        InlineKeyboardButton('📈 Сравнение', callback_data='stats_comparison')
    )
    keyboard.add(
        InlineKeyboardButton('📂 По категориям', callback_data='stats_categories'),
        InlineKeyboardButton('📅 Расходы сегодня', callback_data='stats_today')
    )
    return keyboard

def get_period_selection_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=3)
    keyboard.add(
        InlineKeyboardButton('📅 Сегодня', callback_data='period_today'),
        InlineKeyboardButton('📆 Неделя', callback_data='period_week'),
        InlineKeyboardButton('📊 Месяц', callback_data='period_month')
    )
    keyboard.add(
        InlineKeyboardButton('📈 Все время', callback_data='period_all'),
        InlineKeyboardButton('🔙 Назад', callback_data='back_to_stats_menu')
    )
    return keyboard

def get_partner_view_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton('💸 Расходы партнера', callback_data='partner_expenses'),
        InlineKeyboardButton('💵 Доходы партнера', callback_data='partner_incomes')
    )
    keyboard.add(
        InlineKeyboardButton('📅 Планы партнера', callback_data='partner_plans'),
        InlineKeyboardButton('🛒 Покупки партнера', callback_data='partner_purchases')
    )
    keyboard.add(
        InlineKeyboardButton('📊 Полная статистика', callback_data='partner_full_stats'),
        InlineKeyboardButton('🔙 Назад', callback_data='back_to_main')
    )
    return keyboard

def get_combined_stats_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton('📈 Общие расходы', callback_data='combined_expenses'),
        InlineKeyboardButton('💰 Общие доходы', callback_data='combined_incomes')
    )
    keyboard.add(
        InlineKeyboardButton('📊 Сравнение по категориям', callback_data='combined_categories'),
        InlineKeyboardButton('📋 Итоги за месяц', callback_data='combined_monthly')
    )
    keyboard.add(
        InlineKeyboardButton('📅 Совместные планы', callback_data='combined_plans'),
        InlineKeyboardButton('🔙 Назад', callback_data='back_to_stats')
    )
    return keyboard

def get_priority_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=3)
    keyboard.add(
        InlineKeyboardButton('🔴 Высокий', callback_data='priority_high'),
        InlineKeyboardButton('🟡 Средний', callback_data='priority_medium'),
        InlineKeyboardButton('🟢 Низкий', callback_data='priority_low')
    )
    return keyboard

def get_transactions_view_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton('📅 Сегодня', callback_data='view_today'),
        InlineKeyboardButton('📆 Неделя', callback_data='view_week'),
        InlineKeyboardButton('📊 Месяц', callback_data='view_month'),
        InlineKeyboardButton('📈 Все время', callback_data='view_all')
    )
    return keyboard

def get_purchase_actions_keyboard(purchase_id):
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton('✅ Куплено', callback_data=f'buy_{purchase_id}'),
        InlineKeyboardButton('❌ Удалить', callback_data=f'delete_purchase_{purchase_id}')
    )
    return keyboard