import re
from datetime import datetime
from typing import Optional, Union, Tuple
from decimal import Decimal, InvalidOperation
from .exceptions import ValidationError

class Validators:
    @staticmethod
    def validate_amount(amount_str: str) -> Decimal:
        """Валидация суммы"""
        try:
            # Заменяем запятую на точку и удаляем пробелы
            cleaned = amount_str.replace(',', '.').replace(' ', '')
            amount = Decimal(cleaned)
            
            if amount <= 0:
                raise ValidationError("Сумма должна быть больше 0")
            
            if amount > Decimal('1000000000'):  # 1 миллиард
                raise ValidationError("Сумма слишком большая")
            
            # Округляем до 2 знаков после запятой
            return amount.quantize(Decimal('0.01'))
            
        except (InvalidOperation, ValueError):
            raise ValidationError("Некорректная сумма. Пример: 1500.50 или 1500,50")
    
    @staticmethod
    def validate_date(date_str: str) -> Tuple[str, bool]:
        """Валидация даты"""
        date_str = date_str.lower().strip()
        
        special_dates = {
            'сегодня': datetime.now().date(),
            'завтра': datetime.now().date().replace(day=datetime.now().date().day + 1),
            'послезавтра': datetime.now().date().replace(day=datetime.now().date().day + 2),
        }
        
        if date_str in special_dates:
            return special_dates[date_str].isoformat(), True
        
        try:
            # Пробуем разные форматы
            for fmt in ('%Y-%m-%d', '%d.%m.%Y', '%d/%m/%Y'):
                try:
                    date_obj = datetime.strptime(date_str, fmt).date()
                    # Проверяем, что дата не в прошлом (для планов/покупок)
                    if date_obj < datetime.now().date():
                        raise ValidationError("Дата не может быть в прошлом")
                    return date_obj.isoformat(), False
                except ValueError:
                    continue
            
            raise ValidationError("Неверный формат даты. Используйте ГГГГ-ММ-ДД или ДД.ММ.ГГГГ")
            
        except Exception as e:
            raise ValidationError(f"Ошибка валидации даты: {str(e)}")
    
    @staticmethod
    def validate_time(time_str: str) -> Optional[str]:
        """Валидация времени"""
        if not time_str or time_str.strip() == '-':
            return None
        
        time_str = time_str.strip()
        try:
            datetime.strptime(time_str, '%H:%M')
            return time_str
        except ValueError:
            raise ValidationError("Неверный формат времени. Используйте ЧЧ:ММ")
    
    @staticmethod
    def validate_text(text: str, field_name: str = "текст", max_length: int = 500, 
                     allow_empty: bool = False) -> Optional[str]:
        """Валидация текста"""
        if not text and allow_empty:
            return None
        
        if not text:
            raise ValidationError(f"{field_name} не может быть пустым")
        
        text = text.strip()
        
        if len(text) > max_length:
            raise ValidationError(f"{field_name} слишком длинный (максимум {max_length} символов)")
        
        # Проверка на опасные символы (базовая защита от инъекций)
        dangerous_patterns = [
            (';', "точка с запятой"),
            ('--', "двойной дефис"),
            ('/*', "комментарий SQL"),
            ('*/', "комментарий SQL"),
            ('xp_', "расширенная процедура SQL"),
        ]
        
        for pattern, description in dangerous_patterns:
            if pattern in text.lower():
                raise ValidationError(f"Текст содержит запрещенные символы ({description})")
        
        return text
    
    @staticmethod
    def validate_category(category: str, allowed_categories: list) -> str:
        """Валидация категории"""
        category = category.strip()
        if category not in allowed_categories:
            raise ValidationError(f"Категория должна быть одной из: {', '.join(allowed_categories)}")
        return category
    
    @staticmethod
    def validate_priority(priority: str) -> str:
        """Валидация приоритета"""
        priority = priority.strip().lower()
        if priority not in ['low', 'medium', 'high']:
            raise ValidationError("Приоритет должен быть: low, medium или high")
        return priority