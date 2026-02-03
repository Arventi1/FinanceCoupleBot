import logging
from datetime import datetime, timedelta
from typing import List
from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from database.repository import PlanRepository
from config import config

logger = logging.getLogger(__name__)

class NotificationService:
    """Сервис для управления уведомлениями"""
    
    def __init__(self, bot: Bot):
        self.bot = bot
        self.scheduler = AsyncIOScheduler()
    
    async def check_daily_reminders(self):
        """Проверка ежедневных напоминаний"""
        try:
            today = datetime.now().date()
            
            # Здесь можно получить планы на сегодня и отправить уведомления
            # Примерная реализация
            
            logger.info("✅ Проверка напоминаний выполнена")
            
        except Exception as e:
            logger.error(f"❌ Ошибка при проверке напоминаний: {e}")
    
    async def send_reminder(self, user_id: int, message: str):
        """Отправка напоминания пользователю"""
        try:
            await self.bot.send_message(
                user_id,
                f"🔔 Напоминание!\n\n{message}",
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.error(f"❌ Не удалось отправить напоминание пользователю {user_id}: {e}")
    
    async def schedule_all(self):
        """Запланировать все уведомления"""
        if not self.scheduler.running:
            self.scheduler.start()
        
        # Ежедневная проверка в 9:00
        self.scheduler.add_job(
            self.check_daily_reminders,
            CronTrigger(hour=9, minute=0),
            id='daily_reminders'
        )
        
        # Еженедельная статистика в воскресенье в 20:00
        self.scheduler.add_job(
            self.send_weekly_statistics,
            CronTrigger(day_of_week='sun', hour=20, minute=0),
            id='weekly_stats'
        )
        
        logger.info("✅ Планировщик уведомлений запущен")
    
    async def send_weekly_statistics(self):
        """Отправка еженедельной статистики"""
        try:
            # Здесь можно реализовать отправку статистики за неделю
            pass
        except Exception as e:
            logger.error(f"❌ Ошибка при отправке еженедельной статистики: {e}")