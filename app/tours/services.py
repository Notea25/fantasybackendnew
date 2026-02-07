from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload, joinedload

from app.matches.models import Match
from app.tours.models import Tour
from app.database import async_session_maker
from app.utils.base_service import BaseService
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple, List

class TourService(BaseService):
    model = Tour

    @classmethod
    async def get_current_and_next_tour(cls, league_id: int) -> Tuple[Optional[Tour], Optional[Tour]]:
        now = datetime.utcnow().replace(tzinfo=timezone.utc)

        tour_dates = (
            select(
                Tour.id,
                func.min(Match.date).label("start_date"),
                func.max(Match.date).label("end_date")
            )
            .join(Match, Match.tour_id == Tour.id)
            .where(Tour.league_id == league_id)
            .group_by(Tour.id)
            .subquery()
        )

        stmt = (
            select(Tour, tour_dates.c.start_date, tour_dates.c.end_date)
            .join(tour_dates, Tour.id == tour_dates.c.id)
        )

        async with async_session_maker() as session:
            result = await session.execute(stmt)
            tours = result.unique().all()

            current_tour = None
            next_tour = None
            next_tour_start_date = None

            for tour, start_date, end_date in tours:
                if start_date is None or end_date is None:
                    continue

                if start_date.tzinfo is None:
                    start_date = start_date.replace(tzinfo=timezone.utc)
                if end_date.tzinfo is None:
                    end_date = end_date.replace(tzinfo=timezone.utc)

                if start_date <= now <= end_date:
                    current_tour = tour
                elif start_date > now:
                    if not next_tour or start_date < next_tour_start_date:
                        next_tour = tour
                        next_tour_start_date = start_date

            return current_tour, next_tour

    @classmethod
    async def get_deadline_for_next_tour(cls, league_id: int) -> Optional[datetime]:
        """Get deadline for next tour.
        
        Now reads deadline directly from Tour.deadline field in DB.
        """
        previous_tour, current_tour, next_tour = await cls.get_previous_current_next_tour(league_id=league_id)

        if not next_tour:
            raise HTTPException(
                status_code=404,
                detail=f"No next tour found for league with ID {league_id}"
            )

        if not next_tour.deadline:
            raise HTTPException(
                status_code=404,
                detail=f"Deadline not set for tour {next_tour.id}"
            )

        return next_tour.deadline

    @classmethod
    async def find_one_by_number(cls, number: int, league_id: int) -> Optional[Tour]:
        async with async_session_maker() as session:
            stmt = (
                select(cls.model)
                .where(cls.model.number == number, cls.model.league_id == league_id)
                .options(selectinload(cls.model.matches))
            )
            result = await session.execute(stmt)
            return result.unique().scalars().first()

    @classmethod
    async def find_all_with_relations(cls) -> List[Tour]:
        async with async_session_maker() as session:
            stmt = (
                select(cls.model)
                .options(selectinload(cls.model.matches))
            )
            result = await session.execute(stmt)
            return result.unique().scalars().all()

    @classmethod
    async def find_one_or_none_with_relations(cls, tour_id: int) -> Optional[Tour]:
        async with async_session_maker() as session:
            stmt = (
                select(cls.model)
                .where(cls.model.id == tour_id)
                .options(selectinload(cls.model.matches))
            )
            result = await session.execute(stmt)
            return result.unique().scalars().first()

    @classmethod
    async def find_all_by_league(cls, league_id: int) -> List[Tour]:
        async with async_session_maker() as session:
            stmt = (
                select(cls.model)
                .where(cls.model.league_id == league_id)
                .options(selectinload(cls.model.matches))
            )
            result = await session.execute(stmt)
            return result.unique().scalars().all()

    @classmethod
    async def get_previous_current_next_tour(cls, league_id: int) -> tuple[
        Optional["Tour"], Optional["Tour"], Optional["Tour"]]:
        """Get previous, current and next tour for a league.
        
        New logic:
        - Previous tour: is_started=True AND is_finalized=True (latest by number)
        - Current tour: is_started=True AND is_finalized=False
        - Next tour: is_started=False (earliest by number)
        """
        async with async_session_maker() as session:
            stmt = (
                select(Tour)
                .where(Tour.league_id == league_id)
                .options(selectinload(Tour.matches))
                .order_by(Tour.number)
            )
            result = await session.execute(stmt)
            tours = result.unique().scalars().all()

            current_tour = None
            previous_tour = None
            next_tour = None

            for tour in tours:
                # Current tour: started but not finalized
                if tour.is_started and not tour.is_finalized:
                    current_tour = tour
                
                # Previous tour: started and finalized (take the latest)
                elif tour.is_started and tour.is_finalized:
                    if not previous_tour or tour.number > previous_tour.number:
                        previous_tour = tour
                
                # Next tour: not started (take the earliest)
                elif not tour.is_started:
                    if not next_tour or tour.number < next_tour.number:
                        next_tour = tour

            return previous_tour, current_tour, next_tour
