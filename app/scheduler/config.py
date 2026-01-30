"""
Конфигурация планировщика задач.

Настраивает APScheduler для автоматического выполнения задач.
"""

import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from typing import Optional

from app.scheduler.tour_finalizer import run_tour_finalization

logger = logging.getLogger(__name__)

# Глобальный экземпляр scheduler
scheduler: Optional[AsyncIOScheduler] = None


def get_scheduler() -> AsyncIOScheduler:
    """Получить или создать экземпляр scheduler."""
    global scheduler
    
    if scheduler is None:
        scheduler = AsyncIOScheduler(
            timezone="UTC",
            job_defaults={
                'coalesce': True,  # Объединять пропущенные запуски
                'max_instances': 1,  # Не запускать несколько экземпляров одновременно
                'misfire_grace_time': 3600  # Допустимое опоздание - 1 час
            }
        )
    
    return scheduler


def configure_scheduler():
    """
    Настраивает задачи в scheduler.
    
    По умолчанию финализация туров запускается каждый час.
    Можно изменить расписание через переменные окружения.
    """
    sched = get_scheduler()
    
    # Настройка расписания из переменных окружения
    import os
    
    # Формат cron: минута час день месяц день_недели
    # По умолчанию: каждый час в начале часа (0 * * * *)
    cron_schedule = os.getenv("TOUR_FINALIZATION_CRON", "0 * * * *")
    
    # Парсим cron расписание
    minute, hour, day, month, day_of_week = cron_schedule.split()
    
    # Добавляем задачу финализации туров
    sched.add_job(
        run_tour_finalization,
        trigger=CronTrigger(
            minute=minute,
            hour=hour,
            day=day,
            month=month,
            day_of_week=day_of_week,
            timezone="UTC"
        ),
        id="tour_finalization",
        name="Tour Finalization",
        replace_existing=True
    )
    
    logger.info(f"Scheduled tour finalization: {cron_schedule}")
    
    # Опционально: запуск при старте приложения (для тестирования)
    run_on_startup = os.getenv("RUN_FINALIZATION_ON_STARTUP", "false").lower() == "true"
    
    if run_on_startup:
        sched.add_job(
            run_tour_finalization,
            trigger='date',  # Запуск один раз
            id="tour_finalization_startup",
            name="Tour Finalization (Startup)",
            replace_existing=True
        )
        logger.info("Scheduled tour finalization on startup")


def start_scheduler():
    """Запускает scheduler."""
    sched = get_scheduler()
    
    if not sched.running:
        configure_scheduler()
        sched.start()
        logger.info("Scheduler started")
    else:
        logger.warning("Scheduler is already running")


def shutdown_scheduler():
    """Останавливает scheduler."""
    sched = get_scheduler()
    
    if sched.running:
        sched.shutdown(wait=True)
        logger.info("Scheduler shutdown complete")
    else:
        logger.warning("Scheduler is not running")


def get_scheduled_jobs():
    """
    Получить список запланированных задач.
    
    Returns:
        List of job information
    """
    sched = get_scheduler()
    
    jobs = []
    for job in sched.get_jobs():
        jobs.append({
            "id": job.id,
            "name": job.name,
            "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
            "trigger": str(job.trigger)
        })
    
    return jobs
