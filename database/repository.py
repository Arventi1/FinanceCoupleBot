import logging
from typing import List, Optional, Tuple, Dict, Any
from datetime import datetime, date, timedelta
from decimal import Decimal

from .connection import db_connection
from .models import User, Transaction, Plan, PlannedPurchase
from utils.exceptions import DatabaseError, NotFoundError
from utils.formatters import Formatters

logger = logging.getLogger(__name__)

class BaseRepository:
    """Базовый репозиторий"""
    
    @staticmethod
    async def execute_query(query: str, params: tuple = (), fetch_one: bool = False, 
                          fetch_all: bool = False):
        """Безопасное выполнение запроса с параметрами"""
        try:
            return await db_connection.execute(query, params, fetch_one, fetch_all)
        except Exception as e:
            logger.error(f"Ошибка выполнения запроса: {e}")
            raise

class UserRepository(BaseRepository):
    """Репозиторий для пользователей"""
    
    @classmethod
    async def create_or_update(cls, user_id: int, username: str, full_name: str) -> User:
        """Создать или обновить пользователя"""
        query = """
            INSERT OR REPLACE INTO users (id, username, full_name) 
            VALUES (?, ?, ?)
        """
        await cls.execute_query(query, (user_id, username, full_name))
        
        # Получаем созданного пользователя
        user_data = await cls.get_by_id(user_id)
        if not user_data:
            raise DatabaseError("Не удалось создать пользователя")
        return user_data
    
    @classmethod
    async def get_by_id(cls, user_id: int) -> Optional[User]:
        """Получить пользователя по ID"""
        query = "SELECT * FROM users WHERE id = ?"
        result = await cls.execute_query(query, (user_id,), fetch_one=True)
        
        if result:
            return User(
                id=result['id'],
                username=result['username'],
                full_name=result['full_name'],
                created_at=datetime.fromisoformat(result['created_at'])
            )
        return None
    
    @classmethod
    async def get_allowed_users(cls) -> List[int]:
        """Получить список разрешенных пользователей"""
        query = "SELECT id FROM users"
        results = await cls.execute_query(query, fetch_all=True)
        return [row['id'] for row in results] if results else []

class TransactionRepository(BaseRepository):
    """Репозиторий для транзакций"""
    
    @classmethod
    def _row_to_transaction(cls, row) -> Transaction:
        """Преобразование строки в объект Transaction"""
        return Transaction(
            id=row['id'],
            user_id=row['user_id'],
            type=row['type'],
            amount=Decimal(str(row['amount'])),
            category=row['category'],
            description=row['description'],
            date=datetime.fromisoformat(row['date']).date(),
            is_deleted=bool(row['is_deleted']),
            created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None,
            updated_at=datetime.fromisoformat(row['updated_at']) if row['updated_at'] else None
        )
    
    @classmethod
    async def create(cls, user_id: int, trans_type: str, amount: Decimal, 
                    category: str, description: Optional[str] = None) -> Transaction:
        """Создать транзакцию"""
        query = """
            INSERT INTO transactions (user_id, type, amount, category, description, date)
            VALUES (?, ?, ?, ?, ?, DATE('now'))
        """
        transaction_id = await cls.execute_query(
            query, (user_id, trans_type, str(amount), category, description)
        )
        
        transaction = await cls.get_by_id(transaction_id)
        if not transaction:
            raise DatabaseError("Не удалось создать транзакцию")
        return transaction
    
    @classmethod
    async def get_by_id(cls, transaction_id: int) -> Optional[Transaction]:
        """Получить транзакцию по ID"""
        query = "SELECT * FROM transactions WHERE id = ? AND is_deleted = 0"
        result = await cls.execute_query(query, (transaction_id,), fetch_one=True)
        
        if result:
            return cls._row_to_transaction(result)
        return None
    
    @classmethod
    async def update(cls, transaction_id: int, **kwargs) -> bool:
        """Обновить транзакцию"""
        allowed_fields = {'amount', 'category', 'description'}
        
        updates = []
        params = []
        
        for field, value in kwargs.items():
            if field in allowed_fields and value is not None:
                if field == 'amount' and isinstance(value, Decimal):
                    value = str(value)
                updates.append(f"{field} = ?")
                params.append(value)
        
        if not updates:
            return False
        
        updates.append("updated_at = CURRENT_TIMESTAMP")
        query = f"UPDATE transactions SET {', '.join(updates)} WHERE id = ? AND is_deleted = 0"
        params.append(transaction_id)
        
        await cls.execute_query(query, tuple(params))
        return True
    
    @classmethod
    async def delete(cls, transaction_id: int) -> bool:
        """Удалить транзакцию (мягкое удаление)"""
        query = "UPDATE transactions SET is_deleted = 1 WHERE id = ?"
        await cls.execute_query(query, (transaction_id,))
        return True
    
    @classmethod
    async def get_user_transactions(cls, user_id: int, page: int = 1, page_size: int = 10,
                                   trans_type: Optional[str] = None, 
                                   period: Optional[str] = None,
                                   search_query: Optional[str] = None) -> Tuple[List[Transaction], int]:
        """Получить транзакции пользователя с пагинацией и фильтрацией"""
        # Базовый запрос
        where_conditions = ["user_id = ?", "is_deleted = 0"]
        params = [user_id]
        
        # Фильтр по типу
        if trans_type:
            where_conditions.append("type = ?")
            params.append(trans_type)
        
        # Фильтр по периоду
        if period:
            if period == 'today':
                where_conditions.append("date = DATE('now')")
            elif period == 'week':
                where_conditions.append("date >= DATE('now', '-7 days')")
            elif period == 'month':
                where_conditions.append("strftime('%Y-%m', date) = strftime('%Y-%m', 'now')")
            elif period == 'year':
                where_conditions.append("strftime('%Y', date) = strftime('%Y', 'now')")
        
        # Поиск
        if search_query:
            where_conditions.append("(category LIKE ? OR description LIKE ?)")
            search_pattern = f"%{search_query}%"
            params.extend([search_pattern, search_pattern])
        
        where_clause = " AND ".join(where_conditions)
        
        # Получение общего количества
        count_query = f"SELECT COUNT(*) as total FROM transactions WHERE {where_clause}"
        count_result = await cls.execute_query(count_query, tuple(params), fetch_one=True)
        total = count_result['total'] if count_result else 0
        
        # Получение данных с пагинацией
        offset = (page - 1) * page_size
        data_query = f"""
            SELECT * FROM transactions 
            WHERE {where_clause}
            ORDER BY date DESC, created_at DESC
            LIMIT ? OFFSET ?
        """
        params.extend([page_size, offset])
        
        results = await cls.execute_query(data_query, tuple(params), fetch_all=True)
        
        transactions = []
        if results:
            for row in results:
                transactions.append(cls._row_to_transaction(row))
        
        return transactions, total
    
    @classmethod
    async def get_statistics(cls, user_id: int, period: str = 'month') -> Dict[str, Any]:
        """Получить статистику за период"""
        period_conditions = {
            'today': "date = DATE('now')",
            'week': "date >= DATE('now', '-7 days')",
            'month': "strftime('%Y-%m', date) = strftime('%Y-%m', 'now')",
            'year': "strftime('%Y', date) = strftime('%Y', 'now')",
            'all': "1=1"
        }
        
        condition = period_conditions.get(period, period_conditions['month'])
        
        query = f"""
            SELECT 
                type,
                category,
                SUM(amount) as total,
                COUNT(*) as count
            FROM transactions 
            WHERE user_id = ? AND {condition} AND is_deleted = 0
            GROUP BY type, category
            ORDER BY type, total DESC
        """
        
        results = await cls.execute_query(query, (user_id,), fetch_all=True)
        
        income_total = Decimal('0')
        expense_total = Decimal('0')
        categories = {'income': {}, 'expense': {}}
        
        if results:
            for row in results:
                trans_type = row['type']
                category = row['category']
                total = Decimal(str(row['total']))
                
                if trans_type == 'income':
                    income_total += total
                else:
                    expense_total += total
                
                if category not in categories[trans_type]:
                    categories[trans_type][category] = {'total': total, 'count': row['count']}
                else:
                    categories[trans_type][category]['total'] += total
                    categories[trans_type][category]['count'] += row['count']
        
        return {
            'income_total': income_total,
            'expense_total': expense_total,
            'balance': income_total - expense_total,
            'categories': categories,
            'period': period
        }

# Аналогичные репозитории для Plan и PlannedPurchase...
# (опущено для краткости, но структура аналогична)

class PlanRepository(BaseRepository):
    """Репозиторий для планов"""
    # ... аналогичные методы

class PurchaseRepository(BaseRepository):
    """Репозиторий для покупок"""
    # ... аналогичные методы