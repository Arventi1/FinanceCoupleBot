from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
from database import get_today_reminders

scheduler = AsyncIOScheduler()

async def check_and_send_reminders(bot):
    reminders = get_today_reminders()
    
    for reminder in reminders:
        user_id = reminder[1]
        title = reminder[2]
        description = reminder[3]
        notification_time = reminder[7]
        
        current_time = datetime.now().strftime('%H:%M')
        
        if notification_time and notification_time <= current_time:
            message = f"🔔 Напоминание!\n\n{title}"
            if description:
                message += f"\n{description}"
            
            try:
                await bot.send_message(user_id, message)
            except Exception as e:
                print(f"Ошибка отправки напоминания: {e}")

async def schedule_reminders(bot):
    scheduler.add_job(
        check_and_send_reminders,
        CronTrigger(minute='*/30'),
        args=[bot]
    )
    scheduler.start()
