"""
Планировщик для автоматической финализации туров.

Этот модуль проверяет завершенные туры и автоматически создает snapshots
для следующих туров.
"""

import logging
from datetime import datetime, timezone
from typing import Optional

from app.squads.services import SquadService
from app.tours.services import TourService
from app.leagues.services import LeagueService
from app.database import async_session_maker

logger = logging.getLogger(__name__)


class TourFinalizer:
    """Класс для автоматической финализации туров."""
    
    @staticmethod
    async def finalize_completed_tours() -> dict:
        """
        Проверяет и финализирует завершенные туры для всех лиг.
        
        Логика:
        1. Получает список всех активных лиг
        2. Для каждой лиги проверяет состояние туров
        3. Если текущий тур завершен и есть следующий - финализирует
        
        Returns:
            dict с информацией о финализированных турах
        """
        logger.info("Starting automatic tour finalization check")
        
        total_finalized = 0
        total_created = 0
        leagues_processed = 0
        errors = []
        
        try:
            # Получаем все активные лиги
            leagues = await LeagueService.find_all()
            logger.info(f"Found {len(leagues)} leagues to check")
            
            for league in leagues:
                try:
                    await TourFinalizer._process_league(
                        league,
                        lambda f, c: (
                            total_finalized := total_finalized + f,
                            total_created := total_created + c
                        )
                    )
                    leagues_processed += 1
                    
                except Exception as e:
                    error_msg = f"Error processing league {league.id}: {str(e)}"
                    logger.error(error_msg, exc_info=True)
                    errors.append(error_msg)
            
            result = {
                "timestamp": datetime.utcnow().isoformat(),
                "leagues_processed": leagues_processed,
                "total_finalized_tours": total_finalized,
                "total_created_tours": total_created,
                "errors": errors
            }
            
            logger.info(
                f"Tour finalization completed: "
                f"{total_finalized} finalized, {total_created} created"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Critical error in tour finalization: {str(e)}", exc_info=True)
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e),
                "leagues_processed": leagues_processed
            }
    
    @staticmethod
    async def _process_league(league, stats_callback=None) -> None:
        """
        Обрабатывает одну лигу - проверяет и финализирует туры.
        
        Args:
            league: Объект лиги
            stats_callback: Callback для обновления статистики
        """
        logger.debug(f"Processing league {league.id} ({league.name})")
        
        # Получаем состояние туров
        previous_tour, current_tour, next_tour = await TourService.get_previous_current_next_tour(
            league.id
        )
        
        # Проверяем, есть ли тур для финализации
        tour_to_finalize = None
        
        if current_tour:
            # Проверяем, завершен ли текущий тур
            if await TourFinalizer._is_tour_finished(current_tour):
                tour_to_finalize = current_tour
                logger.info(f"Current tour {current_tour.id} is finished for league {league.id}")
        
        # Если текущего тура нет, но есть предыдущий который еще не финализирован
        elif previous_tour and next_tour:
            # Проверяем, был ли уже финализирован предыдущий тур
            was_finalized = await TourFinalizer._check_if_tour_finalized(
                previous_tour.id, 
                next_tour.id
            )
            if not was_finalized:
                tour_to_finalize = previous_tour
                logger.info(
                    f"Previous tour {previous_tour.id} needs finalization for league {league.id}"
                )
        
        # Финализируем тур если нужно
        if tour_to_finalize and next_tour:
            try:
                result = await SquadService.finalize_tour_for_all_squads(
                    tour_id=tour_to_finalize.id,
                    next_tour_id=next_tour.id
                )
                
                logger.info(
                    f"Finalized tour {tour_to_finalize.id} -> {next_tour.id} "
                    f"for league {league.id}: {result}"
                )
                
                if stats_callback:
                    stats_callback(
                        result['finalized_tours'],
                        result['created_tours']
                    )
                    
            except Exception as e:
                logger.error(
                    f"Failed to finalize tour {tour_to_finalize.id} "
                    f"for league {league.id}: {str(e)}",
                    exc_info=True
                )
                raise
        else:
            logger.debug(f"No tours to finalize for league {league.id}")
    
    @staticmethod
    async def _is_tour_finished(tour) -> bool:
        """
        Проверяет, завершен ли тур.
        
        Тур считается завершенным если:
        - Все его матчи завершены (дата последнего матча прошла)
        - Прошло достаточно времени после последнего матча (например, 2 часа)
        
        Args:
            tour: Объект тура
            
        Returns:
            True если тур завершен
        """
        if not tour.matches_association:
            return False
        
        now = datetime.utcnow().replace(tzinfo=timezone.utc)
        
        # Получаем дату последнего матча
        end_date = max(
            association.match.date 
            for association in tour.matches_association
        )
        
        # Добавляем буфер времени (2 часа после последнего матча)
        from datetime import timedelta
        buffer = timedelta(hours=2)
        
        return now >= (end_date + buffer)
    
    @staticmethod
    async def _check_if_tour_finalized(tour_id: int, next_tour_id: int) -> bool:
        """
        Проверяет, был ли тур уже финализирован.
        
        Проверяем наличие SquadTour для следующего тура с is_current=True
        
        Args:
            tour_id: ID проверяемого тура
            next_tour_id: ID следующего тура
            
        Returns:
            True если тур уже был финализирован
        """
        from app.squads.models import SquadTour
        from sqlalchemy import select, func
        
        async with async_session_maker() as session:
            # Проверяем, есть ли хотя бы один SquadTour для следующего тура
            stmt = (
                select(func.count(SquadTour.id))
                .where(SquadTour.tour_id == next_tour_id)
            )
            result = await session.execute(stmt)
            count = result.scalar()
            
            return count > 0


async def run_tour_finalization():
    """
    Функция-обертка для запуска финализации туров.
    Используется scheduler'ом.
    """
    try:
        result = await TourFinalizer.finalize_completed_tours()
        logger.info(f"Tour finalization result: {result}")
        return result
    except Exception as e:
        logger.error(f"Tour finalization failed: {str(e)}", exc_info=True)
        raise
