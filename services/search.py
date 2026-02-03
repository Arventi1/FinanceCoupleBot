from typing import List, Dict, Any, Optional
import re
from datetime import datetime
from decimal import Decimal

class SearchService:
    """Сервис для поиска данных"""
    
    @staticmethod
    def normalize_search_query(query: str) -> str:
        """Нормализация поискового запроса"""
        if not query:
            return ""
        
        # Удаляем лишние пробелы
        query = query.strip()
        
        # Приводим к нижнему регистру (для нечувствительного поиска)
        query = query.lower()
        
        # Экранируем специальные символы SQL LIKE
        query = query.replace('%', '\\%').replace('_', '\\_')
        
        return query
    
    @staticmethod
    def build_search_pattern(query: str) -> str:
        """Построение шаблона для поиска"""
        normalized = SearchService.normalize_search_query(query)
        
        if not normalized:
            return ""
        
        # Разбиваем на слова и добавляем wildcards
        words = normalized.split()
        patterns = [f"%{word}%" for word in words if word]
        
        return " ".join(patterns)
    
    @staticmethod
    def search_in_text(text: str, query: str) -> bool:
        """Поиск в тексте"""
        if not text or not query:
            return False
        
        normalized_text = text.lower()
        normalized_query = SearchService.normalize_search_query(query)
        
        # Простой поиск по подстроке
        if normalized_query in normalized_text:
            return True
        
        # Поиск по словам
        query_words = normalized_query.split()
        for word in query_words:
            if word and word in normalized_text:
                return True
        
        return False
    
    @staticmethod
    def filter_transactions(transactions: List[Dict], query: str, 
                           search_fields: List[str] = None) -> List[Dict]:
        """Фильтрация транзакций по поисковому запросу"""
        if not query or not transactions:
            return transactions
        
        if search_fields is None:
            search_fields = ['category', 'description']
        
        normalized_query = SearchService.normalize_search_query(query)
        
        results = []
        for transaction in transactions:
            for field in search_fields:
                if field in transaction and transaction[field]:
                    if SearchService.search_in_text(str(transaction[field]), normalized_query):
                        results.append(transaction)
                        break
        
        return results
    
    @staticmethod
    def search_by_amount(transactions: List[Dict], amount_query: str) -> List[Dict]:
        """Поиск по сумме"""
        if not amount_query or not transactions:
            return transactions
        
        try:
            # Пытаемся извлечь число из запроса
            numbers = re.findall(r'\d+[\.,]?\d*', amount_query)
            if not numbers:
                return []
            
            target_amount = Decimal(numbers[0].replace(',', '.'))
            
            # Ищем транзакции с близкой суммой (±10%)
            results = []
            for transaction in transactions:
                if 'amount' in transaction:
                    amount = Decimal(str(transaction['amount']))
                    if abs(amount - target_amount) / target_amount <= 0.1:
                        results.append(transaction)
            
            return results
            
        except Exception:
            return []