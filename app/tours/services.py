from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload, joinedload

from app.matches.models import Match
from app.tours.models import Tour, TourMatchAssociation
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
            .join(TourMatchAssociation, TourMatchAssociation.tour_id == Tour.id)
            .join(Match, Match.id == TourMatchAssociation.match_id)
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
                    if not next_tour or start_date < next_tour.start_date:
                        next_tour = tour

            return current_tour, next_tour

    @classmethod
    async def get_deadline_for_next_tour(cls, league_id: int) -> Optional[datetime]:
        current_tour, next_tour = await cls.get_current_and_next_tour(league_id=league_id)

        if not next_tour:
            raise HTTPException(
                status_code=404,
                detail=f"No next tour found for league with ID {league_id}"
            )

        tour_start_date = (
            select(func.min(Match.date))
            .join(TourMatchAssociation, Match.id == TourMatchAssociation.match_id)
            .where(TourMatchAssociation.tour_id == next_tour.id)
            .scalar_subquery()
        )

        async with async_session_maker() as session:
            result = await session.execute(select(tour_start_date))
            start_date = result.scalar()

            if start_date is None:
                raise HTTPException(
                    status_code=404,
                    detail=f"No matches found for the next tour in league with ID {league_id}"
                )

            if start_date.tzinfo is None:
                start_date = start_date.replace(tzinfo=timezone.utc)

            return start_date - timedelta(hours=2)

    @classmethod
    async def find_one_by_number(cls, number: int, league_id: int) -> Optional[Tour]:
        async with async_session_maker() as session:
            stmt = (
                select(cls.model)
                .where(cls.model.number == number, cls.model.league_id == league_id)
                .options(selectinload(cls.model.matches_association).joinedload(TourMatchAssociation.match))
            )
            result = await session.execute(stmt)
            return result.unique().scalars().first()

    @classmethod
    async def find_all_with_relations(cls) -> List[Tour]:
        async with async_session_maker() as session:
            stmt = (
                select(cls.model)
                .options(selectinload(cls.model.matches_association).joinedload(TourMatchAssociation.match))
            )
            result = await session.execute(stmt)
            return result.unique().scalars().all()

    @classmethod
    async def find_one_or_none_with_relations(cls, tour_id: int) -> Optional[Tour]:
        async with async_session_maker() as session:
            stmt = (
                select(cls.model)
                .where(cls.model.id == tour_id)
                .options(selectinload(cls.model.matches_association).joinedload(TourMatchAssociation.match))
            )
            result = await session.execute(stmt)
            return result.unique().scalars().first()

    @classmethod
    async def find_all_by_league(cls, league_id: int) -> List[Tour]:
        async with async_session_maker() as session:
            stmt = (
                select(cls.model)
                .where(cls.model.league_id == league_id)
                .options(selectinload(cls.model.matches_association).joinedload(TourMatchAssociation.match))
            )
            result = await session.execute(stmt)
            return result.unique().scalars().all()

    @classmethod
    async def get_previous_current_next_tour(cls, league_id: int) -> tuple[
        Optional["Tour"], Optional["Tour"], Optional["Tour"]]:
        now = datetime.utcnow().replace(tzinfo=timezone.utc)

        async with async_session_maker() as session:
            stmt = (
                select(Tour)
                .where(Tour.league_id == league_id)
                .options(selectinload(Tour.matches_association).joinedload(TourMatchAssociation.match))
                .order_by(Tour.number)
            )
            result = await session.execute(stmt)
            tours = result.unique().scalars().all()

            current_tour = None
            previous_tours = []
            next_tours = []

            for tour in tours:
                if not tour.matches_association:
                    continue

                start_date = min(association.match.date for association in tour.matches_association)
                end_date = max(association.match.date for association in tour.matches_association)

                if start_date <= now <= end_date:
                    current_tour = tour
                elif end_date < now:
                    previous_tours.append((tour, end_date))
                elif start_date > now:
                    next_tours.append((tour, start_date))

            previous_tour = max(previous_tours, key=lambda x: x[1], default=None)
            previous_tour = previous_tour[0] if previous_tour else None

            next_tour = min(next_tours, key=lambda x: x[1], default=None)
            next_tour = next_tour[0] if next_tour else None

            return previous_tour, current_tour, next_tour