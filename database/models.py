from dataclasses import dataclass
from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List

@dataclass
class User:
    id: int
    username: Optional[str]
    full_name: str
    created_at: datetime

@dataclass
class Transaction:
    id: int
    user_id: int
    type: str  # 'income' или 'expense'
    amount: Decimal
    category: str
    description: Optional[str]
    date: date
    is_deleted: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

@dataclass
class Plan:
    id: int
    user_id: int
    title: str
    description: Optional[str]
    date: date
    time: Optional[str]
    category: str
    is_shared: bool = False
    notification_enabled: bool = True
    notification_time: Optional[str] = None
    is_deleted: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

@dataclass
class PlannedPurchase:
    id: int
    user_id: int
    item_name: str
    estimated_cost: Decimal
    priority: str  # 'low', 'medium', 'high'
    target_date: Optional[date]
    notes: Optional[str]
    status: str = 'planned'
    is_deleted: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

# SQL для создания таблиц
CREATE_TABLES_SQL = [
    # Пользователи
    """
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        username TEXT,
        full_name TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    
    # Транзакции
    """
    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        type TEXT NOT NULL CHECK(type IN ('income', 'expense')),
        amount DECIMAL(10, 2) NOT NULL,
        category TEXT NOT NULL,
        description TEXT,
        date DATE NOT NULL DEFAULT CURRENT_DATE,
        is_deleted BOOLEAN NOT NULL DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
    )
    """,
    
    # Планы
    """
    CREATE TABLE IF NOT EXISTS plans (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        description TEXT,
        date DATE NOT NULL,
        time TEXT,
        category TEXT NOT NULL DEFAULT 'личные',
        is_shared BOOLEAN NOT NULL DEFAULT 0,
        notification_enabled BOOLEAN NOT NULL DEFAULT 1,
        notification_time TEXT,
        is_deleted BOOLEAN NOT NULL DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
    )
    """,
    
    # Планируемые покупки
    """
    CREATE TABLE IF NOT EXISTS planned_purchases (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        item_name TEXT NOT NULL,
        estimated_cost DECIMAL(10, 2) NOT NULL,
        priority TEXT NOT NULL CHECK(priority IN ('low', 'medium', 'high')),
        target_date DATE,
        notes TEXT,
        status TEXT NOT NULL DEFAULT 'planned',
        is_deleted BOOLEAN NOT NULL DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
    )
    """
]

# SQL для создания индексов
CREATE_INDEXES_SQL = [
    # Индексы для транзакций
    "CREATE INDEX IF NOT EXISTS idx_transactions_user_id ON transactions (user_id)",
    "CREATE INDEX IF NOT EXISTS idx_transactions_date ON transactions (date)",
    "CREATE INDEX IF NOT EXISTS idx_transactions_type ON transactions (type)",
    "CREATE INDEX IF NOT EXISTS idx_transactions_category ON transactions (category)",
    "CREATE INDEX IF NOT EXISTS idx_transactions_user_date ON transactions (user_id, date)",
    
    # Индексы для планов
    "CREATE INDEX IF NOT EXISTS idx_plans_user_id ON plans (user_id)",
    "CREATE INDEX IF NOT EXISTS idx_plans_date ON plans (date)",
    "CREATE INDEX IF NOT EXISTS idx_plans_user_date ON plans (user_id, date)",
    "CREATE INDEX IF NOT EXISTS idx_plans_shared ON plans (is_shared)",
    
    # Индексы для покупок
    "CREATE INDEX IF NOT EXISTS idx_purchases_user_id ON planned_purchases (user_id)",
    "CREATE INDEX IF NOT EXISTS idx_purchases_status ON planned_purchases (status)",
    "CREATE INDEX IF NOT EXISTS idx_purchases_priority ON planned_purchases (priority)",
    "CREATE INDEX IF NOT EXISTS idx_purchases_target_date ON planned_purchases (target_date)",
]