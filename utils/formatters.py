from decimal import Decimal
from datetime import datetime
from typing import List, Tuple, Any, Optional

class Formatters:
    @staticmethod
    def format_amount(amount: Decimal) -> str:
        """Форматирование суммы"""
        return f"{amount:,.2f}".replace(',', ' ').replace('.', ',')
    
    @staticmethod
    def format_date(date_str: str, with_time: bool = False) -> str:
        """Форматирование даты"""
        try:
            date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            if with_time and hasattr(date_obj, 'time') and date_obj.time():
                return date_obj.strftime('%d.%m.%Y %H:%M')
            return date_obj.strftime('%d.%m.%Y')
        except:
            return date_str
    
    @staticmethod
    def format_transaction(transaction: dict) -> str:
        """Форматирование транзакции"""
        emoji = "💵" if transaction.get('type') == 'income' else "💸"
        amount = Formatters.format_amount(Decimal(str(transaction.get('amount', 0))))
        category = transaction.get('category', '')
        date = Formatters.format_date(transaction.get('date', ''))
        
        result = f"{emoji} {amount} руб. - {category} ({date})"
        
        if transaction.get('description'):
            desc = transaction['description']
            if len(desc) > 30:
                desc = desc[:27] + '...'
            result += f" | {desc}"
        
        return result
    
    @staticmethod
    def format_plan(plan: dict) -> str:
        """Форматирование плана"""
        title = plan.get('title', '')
        if len(title) > 25:
            title = title[:22] + '...'
        
        date = Formatters.format_date(plan.get('date', ''))
        time = f" в {plan.get('time')}" if plan.get('time') else ""
        shared = " 👥" if plan.get('is_shared') else ""
        
        return f"{title}{shared} - {date}{time}"
    
    @staticmethod
    def format_purchase(purchase: dict) -> str:
        """Форматирование покупки"""
        item_name = purchase.get('item_name', '')
        if len(item_name) > 20:
            item_name = item_name[:17] + '...'
        
        amount = Formatters.format_amount(Decimal(str(purchase.get('estimated_cost', 0))))
        
        emoji_map = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}
        emoji = emoji_map.get(purchase.get('priority', 'medium'), '🟡')
        
        date = f" до {Formatters.format_date(purchase.get('target_date', ''))}" if purchase.get('target_date') else ""
        
        return f"{emoji} {item_name} - {amount} руб.{date}"
    
    @staticmethod
    def truncate_text(text: str, max_length: int = 50) -> str:
        """Обрезка текста"""
        if len(text) <= max_length:
            return text
        return text[:max_length-3] + '...'