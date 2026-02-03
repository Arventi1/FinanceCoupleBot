from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import Dict, Any, Optional

def get_pagination_keyboard(page_info: Dict[str, Any], 
                          callback_prefix: str,
                          extra_buttons: list = None) -> InlineKeyboardMarkup:
    """Клавиатура для пагинации"""
    keyboard = InlineKeyboardMarkup(row_width=5)
    
    buttons = []
    
    # Кнопка "Назад"
    if page_info['has_prev']:
        buttons.append(
            InlineKeyboardButton(
                "◀️", 
                callback_data=f"{callback_prefix}_page_{page_info['current_page'] - 1}"
            )
        )
    
    # Информация о странице
    buttons.append(
        InlineKeyboardButton(
            f"{page_info['current_page']}/{page_info['total_pages']}", 
            callback_data="noop"
        )
    )
    
    # Кнопка "Вперед"
    if page_info['has_next']:
        buttons.append(
            InlineKeyboardButton(
                "▶️", 
                callback_data=f"{callback_prefix}_page_{page_info['current_page'] + 1}"
            )
        )
    
    keyboard.row(*buttons)
    
    # Дополнительные кнопки
    if extra_buttons:
        for button in extra_buttons:
            if isinstance(button, list):
                keyboard.row(*button)
            else:
                keyboard.add(button)
    
    return keyboard

def get_search_keyboard(search_query: str = "", 
                       callback_prefix: str = "search") -> InlineKeyboardMarkup:
    """Клавиатура для поиска"""
    keyboard = InlineKeyboardMarkup(row_width=2)
    
    if search_query:
        keyboard.add(
            InlineKeyboardButton(
                f"🔍 Поиск: {search_query[:15]}...", 
                callback_data=f"{callback_prefix}_show"
            )
        )
        keyboard.add(
            InlineKeyboardButton(
                "❌ Очистить поиск", 
                callback_data=f"{callback_prefix}_clear"
            )
        )
    else:
        keyboard.add(
            InlineKeyboardButton(
                "🔍 Начать поиск", 
                callback_data=f"{callback_prefix}_start"
            )
        )
    
    return keyboard