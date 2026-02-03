import asyncio
import logging
import sqlite3
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.utils import executor
from datetime import datetime, date, timedelta

from config import BOT_TOKEN, MY_USER_ID, GIRLFRIEND_USER_ID
from database import *
from keyboards import *
from reminders import schedule_reminders

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Инициализация бота
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# Инициализация базы данных
init_db()

# Проверка авторизации
def is_authorized_user(user_id):
    return user_id in [MY_USER_ID, GIRLFRIEND_USER_ID]

# Определение состояний FSM
class AddExpense(StatesGroup):
    waiting_for_amount = State()
    waiting_for_category = State()
    waiting_for_description = State()

class AddIncome(StatesGroup):
    waiting_for_amount = State()
    waiting_for_category = State()
    waiting_for_description = State()

class AddPlan(StatesGroup):
    waiting_for_title = State()
    waiting_for_description = State()
    waiting_for_date = State()
    waiting_for_time = State()

class AddPurchase(StatesGroup):
    waiting_for_name = State()
    waiting_for_cost = State()
    waiting_for_priority = State()
    waiting_for_date = State()
    waiting_for_notes = State()

# ========== КОМАНДА /START ==========
@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    if not is_authorized_user(message.from_user.id):
        await message.answer("❌ Доступ запрещен. Этот бот предназначен только для определенных пользователей.")
        return
    
    add_user(message.from_user.id, message.from_user.username, message.from_user.full_name)
    
    welcome_text = f"""
👋 Привет, {message.from_user.first_name}!

Я твой личный финансовый помощник и планировщик для двоих!

📌 Что я умею:
• Вести учет расходов и доходов
• Показывать статистику за разные периоды
• Показывать статистику партнера
• Общие финансы и сравнение
• Напоминать о планах
• Вести список желаемых покупок

Используй кнопки ниже или команды:
/add_expense - добавить расход
/add_income - добавить доход
/stats - статистика
/partner_stats - статистика партнера
/shared - общие расходы сегодня
/compare - сравнение финансов
/plans - планы на сегодня
/purchases - список покупок
/last - последние транзакции
/weekly_summary - недельная сводка
"""
    
    await message.answer(welcome_text, reply_markup=get_main_keyboard())

# ========== ДОБАВЛЕНИЕ РАСХОДА ==========
@dp.message_handler(lambda message: message.text == '💰 Добавить расход')
async def add_expense_start(message: types.Message):
    if not is_authorized_user(message.from_user.id):
        return
    
    await AddExpense.waiting_for_amount.set()
    await message.answer("💸 Введите сумму расхода:")

@dp.message_handler(state=AddExpense.waiting_for_amount)
async def process_expense_amount(message: types.Message, state: FSMContext):
    try:
        amount = float(message.text.replace(',', '.'))
        if amount <= 0:
            await message.answer("❌ Сумма должна быть больше 0")
            return
        await state.update_data(amount=amount)
        await AddExpense.next()
        await message.answer("📂 Выберите категорию расхода:", reply_markup=get_expense_categories_keyboard())
    except ValueError:
        await message.answer("❌ Пожалуйста, введите корректную сумму (например: 1500.50)")

@dp.callback_query_handler(lambda c: c.data.startswith('expense_cat_'), state=AddExpense.waiting_for_category)
async def process_expense_category(callback_query: types.CallbackQuery, state: FSMContext):
    category = callback_query.data[11:]  # Убираем 'expense_cat_'
    await state.update_data(category=category)
    await AddExpense.next()
    await bot.send_message(callback_query.from_user.id, "📝 Добавьте описание (или отправьте '-' если не нужно):")
    await callback_query.answer()

@dp.message_handler(state=AddExpense.waiting_for_description)
async def process_expense_description(message: types.Message, state: FSMContext):
    data = await state.get_data()
    description = message.text if message.text != '-' else None
    
    add_transaction(
        user_id=message.from_user.id,
        trans_type='expense',
        amount=data['amount'],
        category=data['category'],
        description=description
    )
    
    await state.finish()
    await message.answer(f"✅ Расход {data['amount']} руб. в категории '{data['category']}' добавлен!", 
                         reply_markup=get_main_keyboard())

# ========== ДОБАВЛЕНИЕ ДОХОДА ==========
@dp.message_handler(lambda message: message.text == '💵 Добавить доход')
async def add_income_start(message: types.Message):
    if not is_authorized_user(message.from_user.id):
        return
    
    await AddIncome.waiting_for_amount.set()
    await message.answer("💰 Введите сумму дохода:")

@dp.message_handler(state=AddIncome.waiting_for_amount)
async def process_income_amount(message: types.Message, state: FSMContext):
    try:
        amount = float(message.text.replace(',', '.'))
        if amount <= 0:
            await message.answer("❌ Сумма должна быть больше 0")
            return
        await state.update_data(amount=amount)
        await AddIncome.next()
        await message.answer("📂 Выберите категорию дохода:", reply_markup=get_income_categories_keyboard())
    except ValueError:
        await message.answer("❌ Пожалуйста, введите корректную сумму (например: 1500.50)")

@dp.callback_query_handler(lambda c: c.data.startswith('income_cat_'), state=AddIncome.waiting_for_category)
async def process_income_category(callback_query: types.CallbackQuery, state: FSMContext):
    category = callback_query.data[10:]  # Убираем 'income_cat_'
    await state.update_data(category=category)
    await AddIncome.next()
    await bot.send_message(callback_query.from_user.id, "📝 Добавьте описание (или отправьте '-' если не нужно):")
    await callback_query.answer()

@dp.message_handler(state=AddIncome.waiting_for_description)
async def process_income_description(message: types.Message, state: FSMContext):
    data = await state.get_data()
    description = message.text if message.text != '-' else None
    
    add_transaction(
        user_id=message.from_user.id,
        trans_type='income',
        amount=data['amount'],
        category=data['category'],
        description=description
    )
    
    await state.finish()
    await message.answer(f"✅ Доход {data['amount']} руб. в категории '{data['category']}' добавлен!", 
                         reply_markup=get_main_keyboard())

# ========== ДОБАВЛЕНИЕ ПЛАНА ==========
@dp.message_handler(lambda message: message.text == '📅 Добавить план')
async def add_plan_start(message: types.Message):
    if not is_authorized_user(message.from_user.id):
        return
    
    await AddPlan.waiting_for_title.set()
    await message.answer("📝 Введите название плана:")

@dp.message_handler(state=AddPlan.waiting_for_title)
async def process_plan_title(message: types.Message, state: FSMContext):
    await state.update_data(title=message.text)
    await AddPlan.next()
    await message.answer("📋 Введите описание плана (или '-' если не нужно):")

@dp.message_handler(state=AddPlan.waiting_for_description)
async def process_plan_description(message: types.Message, state: FSMContext):
    description = message.text if message.text != '-' else None
    await state.update_data(description=description)
    await AddPlan.next()
    await message.answer("📅 Введите дату (в формате ГГГГ-ММ-ДД, или 'сегодня', 'завтра'):")

@dp.message_handler(state=AddPlan.waiting_for_date)
async def process_plan_date(message: types.Message, state: FSMContext):
    date_str = message.text.lower()
    if date_str == 'сегодня':
        plan_date = date.today().isoformat()
    elif date_str == 'завтра':
        plan_date = (date.today() + timedelta(days=1)).isoformat()
    else:
        try:
            datetime.strptime(date_str, '%Y-%m-%d')
            plan_date = date_str
        except ValueError:
            await message.answer("❌ Неверный формат даты. Используйте ГГГГ-ММ-ДД")
            return
    
    await state.update_data(date=plan_date)
    await AddPlan.next()
    await message.answer("⏰ Введите время (в формате ЧЧ:ММ, или '-' если не нужно):")

@dp.message_handler(state=AddPlan.waiting_for_time)
async def process_plan_time(message: types.Message, state: FSMContext):
    data = await state.get_data()
    time_str = message.text if message.text != '-' else None
    
    if time_str and time_str != '-':
        try:
            datetime.strptime(time_str, '%H:%M')
        except ValueError:
            await message.answer("❌ Неверный формат времени. Используйте ЧЧ:ММ")
            return
    
    add_plan(
        user_id=message.from_user.id,
        title=data['title'],
        description=data['description'],
        plan_date=data['date'],
        time=time_str,
        notification_time=time_str
    )
    
    await state.finish()
    await message.answer(f"✅ План '{data['title']}' добавлен на {data['date']}!", 
                         reply_markup=get_main_keyboard())

# ========== ДОБАВЛЕНИЕ ПОКУПКИ ==========
@dp.message_handler(lambda message: message.text == '🛒 Добавить покупку')
async def add_purchase_start(message: types.Message):
    if not is_authorized_user(message.from_user.id):
        return
    
    await AddPurchase.waiting_for_name.set()
    await message.answer("🛍️ Введите название покупки:")

@dp.message_handler(state=AddPurchase.waiting_for_name)
async def process_purchase_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await AddPurchase.next()
    await message.answer("💰 Введите примерную стоимость:")

@dp.message_handler(state=AddPurchase.waiting_for_cost)
async def process_purchase_cost(message: types.Message, state: FSMContext):
    try:
        cost = float(message.text.replace(',', '.'))
        if cost <= 0:
            await message.answer("❌ Стоимость должна быть больше 0")
            return
        await state.update_data(cost=cost)
        await AddPurchase.next()
        await message.answer("🎯 Выберите приоритет:", reply_markup=get_priority_keyboard())
    except ValueError:
        await message.answer("❌ Пожалуйста, введите корректную сумму")

@dp.callback_query_handler(lambda c: c.data.startswith('priority_'), state=AddPurchase.waiting_for_priority)
async def process_purchase_priority(callback_query: types.CallbackQuery, state: FSMContext):
    priority = callback_query.data[9:]  # Убираем 'priority_'
    await state.update_data(priority=priority)
    await AddPurchase.next()
    await bot.send_message(callback_query.from_user.id, "📅 Введите дату, к которой нужна покупка (ГГГГ-ММ-ДД или '-'):")
    await callback_query.answer()

@dp.message_handler(state=AddPurchase.waiting_for_date)
async def process_purchase_date(message: types.Message, state: FSMContext):
    data = await state.get_data()
    date_str = message.text if message.text != '-' else None
    
    if date_str and date_str != '-':
        try:
            datetime.strptime(date_str, '%Y-%m-%d')
        except ValueError:
            await message.answer("❌ Неверный формат даты. Используйте ГГГГ-ММ-ДД")
            return
    
    await state.update_data(date=date_str)
    await AddPurchase.next()
    await message.answer("📝 Добавьте заметки (или отправьте '-' если не нужно):")

@dp.message_handler(state=AddPurchase.waiting_for_notes)
async def process_purchase_notes(message: types.Message, state: FSMContext):
    data = await state.get_data()
    notes = message.text if message.text != '-' else None
    
    add_planned_purchase(
        user_id=message.from_user.id,
        item_name=data['name'],
        estimated_cost=data['cost'],
        priority=data['priority'],
        target_date=data['date'],
        notes=notes
    )
    
    await state.finish()
    await message.answer(f"✅ Покупка '{data['name']}' добавлена в список!", 
                         reply_markup=get_main_keyboard())

# ========== ПРОСМОТР ПЛАНОВ ==========
@dp.message_handler(lambda message: message.text == '📝 Мои планы')
async def show_today_plans(message: types.Message):
    if not is_authorized_user(message.from_user.id):
        return
    
    plans = get_daily_plans(message.from_user.id)
    
    if not plans:
        await message.answer("📭 На сегодня планов нет!")
        return
    
    response = "📅 *Ваши планы на сегодня:*\n\n"
    for plan in plans:
        response += f"• *{plan[2]}*"
        if plan[5]:  # Время
            response += f" в {plan[5]}"
        if plan[3]:  # Описание
            response += f"\n   📝 {plan[3]}"
        response += "\n\n"
    
    await message.answer(response, parse_mode='Markdown')

# ========== ПРОСМОТР ПОКУПОК ==========
@dp.message_handler(lambda message: message.text == '📋 Мои покупки')
async def show_planned_purchases(message: types.Message):
    if not is_authorized_user(message.from_user.id):
        return
    
    purchases = get_planned_purchases(message.from_user.id)
    
    if not purchases:
        await message.answer("🛍️ Список планируемых покупок пуст!")
        return
    
    response = "📋 *Ваши планируемые покупки:*\n\n"
    total = 0
    for purchase in purchases:
        emoji = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}[purchase[4]]
        response += f"{emoji} *{purchase[2]}* - {purchase[3]} руб."
        if purchase[5]:  # Дата
            response += f" (до {purchase[5]})"
        if purchase[6]:  # Заметки
            response += f"\n   📝 {purchase[6]}"
        response += f"\n   🆔 ID: {purchase[0]}\n\n"
        total += purchase[3]
    
    response += f"💵 *Общая сумма: {total} руб.*"
    await message.answer(response, parse_mode='Markdown')

# ========== СТАТИСТИКА ==========
@dp.message_handler(lambda message: message.text == '📊 Статистика')
async def show_statistics_menu(message: types.Message):
    if not is_authorized_user(message.from_user.id):
        return
    
    await message.answer("📊 Выберите тип статистики:", reply_markup=get_statistics_menu_keyboard())

@dp.callback_query_handler(lambda c: c.data.startswith('stats_'))
async def process_stats_menu(callback_query: types.CallbackQuery):
    action = callback_query.data[6:]
    user_id = callback_query.from_user.id
    
    if action == 'my':
        await bot.send_message(user_id, "📊 Выберите период для статистики:", 
                              reply_markup=get_period_selection_keyboard())
    
    elif action == 'partner':
        await bot.send_message(user_id, "👤 *Данные партнера:*", 
                              parse_mode='Markdown', 
                              reply_markup=get_partner_view_keyboard())
    
    elif action == 'combined':
        await bot.send_message(user_id, "👫 *Общая статистика:*", 
                              parse_mode='Markdown', 
                              reply_markup=get_combined_stats_keyboard())
    
    elif action == 'comparison':
        comparison = get_monthly_comparison()
        
        if comparison:
            response = "📊 *Сравнение за месяц:*\n\n"
            total_combined_income = 0
            total_combined_expense = 0
            
            for user_data in comparison:
                username = user_data[0]
                income = user_data[1] or 0
                expense = user_data[2] or 0
                balance = user_data[3] or 0
                
                response += f"*{username}:*\n"
                response += f"  💵 Доходы: {income:.2f} руб.\n"
                response += f"  💸 Расходы: {expense:.2f} руб.\n"
                response += f"  ⚖️ Баланс: {balance:.2f} руб.\n\n"
                
                total_combined_income += income
                total_combined_expense += expense
            
            total_balance = total_combined_income - total_combined_expense
            response += f"*Общие итоги:*\n"
            response += f"  📈 Общий доход: {total_combined_income:.2f} руб.\n"
            response += f"  📉 Общий расход: {total_combined_expense:.2f} руб.\n"
            response += f"  ⚖️ Общий баланс: {total_balance:.2f} руб."
        else:
            response = "📊 Данных для сравнения нет"
        
        await bot.send_message(user_id, response, parse_mode='Markdown')
    
    elif action == 'categories':
        categories_stats = get_common_categories_statistics()
        
        if categories_stats:
            response = "📂 *Топ категорий по расходам за месяц:*\n\n"
            total_expenses = 0
            
            for i, (category, expense, count) in enumerate(categories_stats, 1):
                if expense > 0:
                    total_expenses += expense
                    response += f"{i}. *{category}:* {expense:.2f} руб. ({count} записей)\n"
            
            response += f"\n💸 *Всего расходов:* {total_expenses:.2f} руб."
        else:
            response = "📊 Данных по категориям нет"
        
        await bot.send_message(user_id, response, parse_mode='Markdown')
    
    elif action == 'today':
        today_expenses = get_daily_combined_expenses()
        
        if today_expenses:
            response = "📅 *Расходы за сегодня:*\n\n"
            current_user = None
            user_total = 0
            overall_total = 0
            
            for expense in today_expenses:
                username, category, amount, description, created_at = expense
                
                if username != current_user:
                    if current_user:
                        response += f"*Итого: {user_total:.2f} руб.*\n\n"
                        user_total = 0
                    current_user = username
                    response += f"*👤 {username}:*\n"
                
                user_total += amount
                overall_total += amount
                
                desc = f" - {description}" if description else ""
                response += f"  • {category}: {amount:.2f} руб.{desc}\n"
            
            if current_user:
                response += f"\n*Итого: {user_total:.2f} руб.*"
            
            response += f"\n\n💰 *Общая сумма: {overall_total:.2f} руб.*"
        else:
            response = "💸 *Сегодня еще не было расходов*"
        
        await bot.send_message(user_id, response, parse_mode='Markdown')
    
    await callback_query.answer()

# ========== СТАТИСТИКА ПО ПЕРИОДАМ ==========
@dp.callback_query_handler(lambda c: c.data.startswith('period_'))
async def process_period_statistics(callback_query: types.CallbackQuery):
    action = callback_query.data[7:]  # Убираем 'period_'
    user_id = callback_query.from_user.id
    
    if action == 'today':
        period_text = "сегодня"
    elif action == 'week':
        period_text = "неделю"
    elif action == 'month':
        period_text = "месяц"
    elif action == 'all':
        period_text = "всё время"
    else:
        period_text = "период"
    
    # Получаем статистику за период
    stats = get_period_statistics(user_id, action)
    
    if stats and (stats[0] or stats[1]):
        total_income = stats[0] or 0
        total_expense = stats[1] or 0
        count = stats[2] or 0
        balance = total_income - total_expense
        
        response = f"""
📊 *Статистика за {period_text}:*

📈 *Доходы:* {total_income:.2f} руб.
📉 *Расходы:* {total_expense:.2f} руб.
💰 *Баланс:* {balance:.2f} руб.
📋 *Количество операций:* {count}
        """
        
        # Получаем детализированный список
        transactions = get_transactions(user_id, action)
        
        if transactions:
            response += "\n\n📝 *Детали операций:*\n\n"
            
            if action == 'today':
                for trans in transactions:
                    trans_type, amount, category, description, time = trans
                    emoji = "💵" if trans_type == 'income' else "💸"
                    desc = f"\n   📝 {description}" if description else ""
                    response += f"{emoji} *{category}:* {amount:.2f} руб. ({time}){desc}\n"
            else:
                current_date = None
                for trans in transactions:
                    if action == 'week' or action == 'month':
                        trans_type, amount, category, description, trans_date, time = trans
                    else:
                        trans_type, amount, category, description, time = trans
                        trans_date = "Сегодня"
                    
                    if trans_date != current_date:
                        current_date = trans_date
                        response += f"\n📅 *{trans_date}:*\n"
                    
                    emoji = "💵" if trans_type == 'income' else "💸"
                    desc = f"\n   📝 {description}" if description else ""
                    time_str = f" ({time})" if time else ""
                    response += f"   {emoji} *{category}:* {amount:.2f} руб.{time_str}{desc}\n"
    else:
        response = f"📊 *Нет данных за {period_text}*"
    
    await bot.send_message(user_id, response, parse_mode='Markdown')
    await callback_query.answer()

# ========== ПРОСМОТР ДАННЫХ ПАРТНЕРА ==========
@dp.callback_query_handler(lambda c: c.data.startswith('partner_'))
async def process_partner_view(callback_query: types.CallbackQuery):
    action = callback_query.data[8:]
    user_id = callback_query.from_user.id
    
    if user_id == MY_USER_ID:
        partner_id = GIRLFRIEND_USER_ID
    else:
        partner_id = MY_USER_ID
    
    if action == 'expenses':
        expenses = get_partner_transactions(user_id, 'month')
        
        if expenses:
            response = "💸 *Расходы партнера за месяц:*\n\n"
            total = 0
            
            for category, amount, count in expenses:
                if amount:
                    total += amount
                    response += f"• *{category}:* {amount:.2f} руб. ({count} записей)\n"
            
            response += f"\n💰 *Всего: {total:.2f} руб.*"
        else:
            response = "📭 У партнера нет расходов за месяц"
        
        await bot.send_message(user_id, response, parse_mode='Markdown')
    
    elif action == 'incomes':
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT category, SUM(amount), COUNT(*)
            FROM transactions 
            WHERE user_id = ? 
            AND type = 'income'
            AND strftime('%Y-%m', date) = strftime('%Y-%m', 'now')
            GROUP BY category
            ORDER BY SUM(amount) DESC
        ''', (partner_id,))
        
        incomes = cursor.fetchall()
        conn.close()
        
        if incomes:
            response = "💵 *Доходы партнера за месяц:*\n\n"
            total = 0
            
            for category, amount, count in incomes:
                if amount:
                    total += amount
                    response += f"• *{category}:* {amount:.2f} руб. ({count} записей)\n"
            
            response += f"\n💰 *Всего: {total:.2f} руб.*"
        else:
            response = "📭 У партнера нет доходов за месяц"
        
        await bot.send_message(user_id, response, parse_mode='Markdown')
    
    elif action == 'plans':
        plans = get_daily_plans(partner_id)
        
        if plans:
            response = "📅 *Планы партнера на сегодня:*\n\n"
            for plan in plans:
                response += f"• *{plan[2]}*"
                if plan[5]:
                    response += f" в {plan[5]}"
                if plan[3]:
                    response += f"\n   📝 {plan[3]}"
                response += "\n"
        else:
            response = "📭 У партнера нет планов на сегодня"
        
        await bot.send_message(user_id, response, parse_mode='Markdown')
    
    elif action == 'purchases':
        purchases = get_planned_purchases(partner_id)
        
        if purchases:
            response = "🛒 *Планируемые покупки партнера:*\n\n"
            total = 0
            
            for purchase in purchases:
                emoji = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}[purchase[4]]
                response += f"{emoji} *{purchase[2]}* - {purchase[3]} руб."
                if purchase[5]:
                    response += f" (до {purchase[5]})"
                if purchase[6]:
                    response += f"\n   📝 {purchase[6]}"
                response += "\n"
                total += purchase[3]
            
            response += f"\n💰 *Общая сумма: {total:.2f} руб.*"
        else:
            response = "🛍️ У партнера нет планируемых покупок"
        
        await bot.send_message(user_id, response, parse_mode='Markdown')
    
    elif action == 'full_stats':
        stats = get_period_statistics(partner_id, 'month')
        
        if stats and (stats[0] or stats[1]):
            total_income = stats[0] or 0
            total_expense = stats[1] or 0
            balance = total_income - total_expense
            
            response = f"""
📊 *Полная статистика партнера за месяц:*

💵 *Доходы:* {total_income:.2f} руб.
💸 *Расходы:* {total_expense:.2f} руб.
💰 *Баланс:* {balance:.2f} руб.
            """
        else:
            response = "📊 У партнера нет данных за месяц"
        
        await bot.send_message(user_id, response, parse_mode='Markdown')
    
    await callback_query.answer()

# ========== ОБЩАЯ СТАТИСТИКА ==========
@dp.message_handler(lambda message: message.text == '👫 Общие финансы')
async def show_shared_finances(message: types.Message):
    if not is_authorized_user(message.from_user.id):
        return
    
    await message.answer("👫 *Управление общими финансами:*", 
                        parse_mode='Markdown',
                        reply_markup=get_combined_stats_keyboard())

@dp.callback_query_handler(lambda c: c.data.startswith('combined_'))
async def process_combined_stats(callback_query: types.CallbackQuery):
    action = callback_query.data[9:]
    user_id = callback_query.from_user.id
    
    if action == 'expenses':
        shared_expenses = get_shared_expenses_by_category()
        
        if shared_expenses:
            response = "👫 *Общие расходы по категориям за месяц:*\n\n"
            total_expenses = 0
            
            for category, user1, user2, total in shared_expenses:
                if total > 0:
                    total_expenses += total
                    response += f"*{category}:*\n"
                    response += f"  Вы: {user1:.2f} руб.\n"
                    response += f"  Партнер: {user2:.2f} руб.\n"
                    response += f"  Всего: {total:.2f} руб.\n\n"
            
            response += f"💰 *Общая сумма расходов: {total_expenses:.2f} руб.*"
        else:
            response = "📊 Нет общих расходов за месяц"
        
        await bot.send_message(user_id, response, parse_mode='Markdown')
    
    elif action == 'incomes':
        combined_stats = get_combined_statistics('month')
        
        if combined_stats:
            response = "💰 *Общие доходы за месяц:*\n\n"
            total_combined_income = 0
            
            for stats in combined_stats:
                total_income, total_expense, stat_user_id = stats
                if total_income:
                    total_combined_income += total_income
            
            response += f"*Общая сумма доходов: {total_combined_income:.2f} руб.*"
        else:
            response = "📊 Нет данных о доходах"
        
        await bot.send_message(user_id, response, parse_mode='Markdown')
    
    elif action == 'categories':
        shared_expenses = get_shared_expenses_by_category()
        
        if shared_expenses:
            response = "📊 *Сравнение расходов по категориям:*\n\n"
            
            for category, user1, user2, total in shared_expenses:
                if total > 0:
                    user1_percent = (user1 / total * 100) if total > 0 else 0
                    user2_percent = (user2 / total * 100) if total > 0 else 0
                    
                    response += f"*{category} ({total:.2f} руб.):*\n"
                    response += f"  Вы: {user1:.2f} руб. ({user1_percent:.1f}%)\n"
                    response += f"  Партнер: {user2:.2f} руб. ({user2_percent:.1f}%)\n\n"
        else:
            response = "📊 Нет данных для сравнения"
        
        await bot.send_message(user_id, response, parse_mode='Markdown')
    
    elif action == 'monthly':
        comparison = get_monthly_comparison()
        
        if comparison:
            response = "📈 *Общие итоги за месяц:*\n\n"
            total_combined_income = 0
            total_combined_expense = 0
            
            for user_data in comparison:
                username = user_data[0]
                income = user_data[1] or 0
                expense = user_data[2] or 0
                
                total_combined_income += income
                total_combined_expense += expense
                
                response += f"*{username}:*\n"
                response += f"  💵 Доходы: {income:.2f} руб.\n"
                response += f"  💸 Расходы: {expense:.2f} руб.\n"
                response += f"  ⚖️ Баланс: {income - expense:.2f} руб.\n\n"
            
            total_balance = total_combined_income - total_combined_expense
            savings_rate = (total_balance / total_combined_income * 100) if total_combined_income > 0 else 0
            
            response += "👫 *Вместе:*\n"
            response += f"  💰 Общий доход: {total_combined_income:.2f} руб.\n"
            response += f"  💸 Общий расход: {total_combined_expense:.2f} руб.\n"
            response += f"  ⚖️ Общий баланс: {total_balance:.2f} руб.\n"
            response += f"  📈 Норма сбережений: {savings_rate:.1f}%\n\n"
            
            if total_balance > 0:
                response += "✅ *Отличный результат! Вы сберегаете деньги!*"
            else:
                response += "⚠️ *Внимание! Расходы превышают доходы.*"
        else:
            response = "📊 Нет данных за месяц"
        
        await bot.send_message(user_id, response, parse_mode='Markdown')
    
    elif action == 'plans':
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT p.*, u.full_name 
            FROM plans p
            JOIN users u ON p.user_id = u.id
            WHERE p.date >= DATE('now')
            AND p.user_id IN (?, ?)
            ORDER BY p.date, p.time
            LIMIT 10
        ''', (MY_USER_ID, GIRLFRIEND_USER_ID))
        
        plans = cursor.fetchall()
        conn.close()
        
        if plans:
            response = "📅 *Ближайшие совместные планы:*\n\n"
            current_date = None
            
            for plan in plans:
                plan_date = plan[4]
                if plan_date != current_date:
                    current_date = plan_date
                    response += f"\n*📅 {plan_date}:*\n"
                
                username = plan[9]
                time_str = f" в {plan[5]}" if plan[5] else ""
                response += f"  👤 {username}: {plan[2]}{time_str}\n"
                if plan[3]:
                    response += f"     📝 {plan[3]}\n"
        else:
            response = "📭 Нет совместных планов на будущее"
        
        await bot.send_message(user_id, response, parse_mode='Markdown')
    
    await callback_query.answer()

# ========== КОМАНДЫ ==========
@dp.message_handler(commands=['shared'])
async def cmd_shared(message: types.Message):
    """Общие расходы сегодня"""
    if not is_authorized_user(message.from_user.id):
        return
    
    today_expenses = get_daily_combined_expenses()
    
    if today_expenses:
        response = "👫 *Общие расходы сегодня:*\n\n"
        user_totals = {}
        overall_total = 0
        
        for expense in today_expenses:
            username, category, amount, description, created_at = expense
            
            if username not in user_totals:
                user_totals[username] = 0
            
            user_totals[username] += amount
            overall_total += amount
        
        for username, total in user_totals.items():
            response += f"*{username}:* {total:.2f} руб.\n"
        
        response += f"\n💰 *Всего: {overall_total:.2f} руб.*"
    else:
        response = "💸 *Сегодня еще не было общих расходов*"
    
    await message.answer(response, parse_mode='Markdown')

@dp.message_handler(commands=['last'])
async def cmd_last_transactions(message: types.Message):
    """Последние транзакции"""
    if not is_authorized_user(message.from_user.id):
        return
    
    transactions = get_recent_transactions(message.from_user.id, 10)
    
    if not transactions:
        await message.answer("📭 У вас еще нет транзакций")
        return
    
    response = "📊 *Последние 10 транзакций:*\n\n"
    
    for trans in transactions:
        trans_type, amount, category, description, datetime_str = trans
        
        emoji = "💵" if trans_type == 'income' else "💸"
        type_text = "Доход" if trans_type == 'income' else "Расход"
        
        response += f"{emoji} *{type_text}: {amount:.2f} руб.*\n"
        response += f"   📂 Категория: {category}\n"
        response += f"   📅 Дата: {datetime_str}\n"
        if description:
            response += f"   📝 Описание: {description}\n"
        response += "\n"
    
    await message.answer(response, parse_mode='Markdown')

@dp.message_handler(commands=['weekly_summary'])
async def cmd_weekly_summary(message: types.Message):
    """Недельная сводка"""
    if not is_authorized_user(message.from_user.id):
        return
    
    weekly_data = get_weekly_summary()
    
    if weekly_data:
        response = "📊 *Еженедельная сводка (последние 4 недели):*\n\n"
        
        current_week = None
        for data in weekly_data:
            username, week_start, income, expense = data
            
            if week_start != current_week:
                current_week = week_start
                response += f"\n*📅 Неделя с {week_start}:*\n"
            
            balance = income - expense
            response += f"  👤 {username}:\n"
            response += f"    💵 Доходы: {income:.2f} руб.\n"
            response += f"    💸 Расходы: {expense:.2f} руб.\n"
            response += f"    ⚖️ Баланс: {balance:.2f} руб.\n"
    else:
        response = "📊 Нет данных за последние 4 недели"
    
    await message.answer(response, parse_mode='Markdown')

# ========== КНОПКИ НАЗАД ==========
@dp.callback_query_handler(lambda c: c.data.startswith('back_'))
async def process_back_button(callback_query: types.CallbackQuery):
    action = callback_query.data[5:]
    user_id = callback_query.from_user.id
    
    if action == 'to_main':
        await bot.send_message(user_id, "Главное меню:", reply_markup=get_main_keyboard())
    
    elif action == 'to_stats':
        await bot.send_message(user_id, "📊 Выберите тип статистики:", 
                              reply_markup=get_statistics_menu_keyboard())
    
    elif action == 'to_stats_menu':
        await bot.send_message(user_id, "📊 Меню статистики:", 
                              reply_markup=get_statistics_menu_keyboard())
    
    await callback_query.answer()

# ========== ЗАПУСК БОТА ==========
async def on_startup(dp):
    try:
        await schedule_reminders(bot)
        logging.info("Бот запущен!")
    except Exception as e:
        logging.error(f"Ошибка при запуске планировщика: {e}")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)