import aiosqlite
import logging
from typing import Optional, AsyncGenerator
from contextlib import asynccontextmanager
from config import config
from utils.exceptions import DatabaseError

logger = logging.getLogger(__name__)

class DatabaseConnection:
    """Управление подключением к SQLite"""
    
    _instance: Optional['DatabaseConnection'] = None
    _db: Optional[aiosqlite.Connection] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    async def initialize(self):
        """Инициализация подключения"""
        try:
            self._db = await aiosqlite.connect(config.DB_PATH)
            self._db.row_factory = aiosqlite.Row
            await self._db.execute("PRAGMA foreign_keys = ON")
            await self._db.execute("PRAGMA journal_mode = WAL")
            await self._db.execute("PRAGMA synchronous = NORMAL")
            await self._db.commit()
            logger.info("✅ База данных подключена")
        except Exception as e:
            logger.error(f"❌ Ошибка подключения к БД: {e}")
            raise DatabaseError(f"Не удалось подключиться к БД: {e}")
    
    async def close(self):
        """Закрытие подключения"""
        if self._db:
            await self._db.close()
            self._db = None
    
    @asynccontextmanager
    async def get_connection(self):
        """Контекстный менеджер для получения подключения"""
        if not self._db:
            await self.initialize()
        
        try:
            yield self._db
        except aiosqlite.Error as e:
            logger.error(f"❌ Ошибка SQLite: {e}")
            raise DatabaseError(f"Ошибка базы данных: {e}")
        except Exception as e:
            logger.error(f"❌ Неизвестная ошибка БД: {e}")
            raise DatabaseError(f"Неизвестная ошибка: {e}")
    
    async def execute(self, query: str, params: tuple = (), fetch_one: bool = False, fetch_all: bool = False):
        """Выполнение запроса с обработкой ошибок"""
        async with self.get_connection() as db:
            try:
                cursor = await db.execute(query, params)
                await db.commit()
                
                if fetch_one:
                    return await cursor.fetchone()
                elif fetch_all:
                    return await cursor.fetchall()
                else:
                    return cursor.lastrowid
                    
            except aiosqlite.IntegrityError as e:
                logger.error(f"❌ Ошибка целостности данных: {e}")
                raise DatabaseError(f"Ошибка целостности данных: {e}")
            except aiosqlite.OperationalError as e:
                logger.error(f"❌ Операционная ошибка БД: {e}")
                raise DatabaseError(f"Операционная ошибка: {e}")
            except Exception as e:
                logger.error(f"❌ Неизвестная ошибка при выполнении запроса: {e}")
                raise DatabaseError(f"Неизвестная ошибка: {e}")

# Синглтон экземпляр
db_connection = DatabaseConnection()