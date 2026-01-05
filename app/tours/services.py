from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.matches.models import Match
from app.teams.models import Team
from app.tours.models import Tour, tour_matches_association
from app.database import async_session_maker
from app.utils.base_service import BaseService

from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple

class TourService(BaseService):
    model = Tour

    @classmethod
    async def get_current_and_next_tour(cls, league_id: int) -> tuple[Tour | None, Tour | None]:
        now = datetime.utcnow().replace(tzinfo=timezone.utc)  # Приводим текущее время к UTC с временной зоной

        # Подзапрос для минимальной и максимальной даты матчей каждого тура
        tour_dates = (
            select(
                tour_matches_association.c.tour_id,
                func.min(Match.date).label("start_date"),
                func.max(Match.date).label("end_date")
            )
            .join(Match, Match.id == tour_matches_association.c.match_id)
            .group_by(tour_matches_association.c.tour_id)
            .subquery()
        )

        # Основной запрос: выбираем все туры с их датами
        stmt = (
            select(Tour, tour_dates.c.start_date, tour_dates.c.end_date)
            .join(tour_dates, Tour.id == tour_dates.c.tour_id)
            .where(Tour.league_id == league_id)
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
    async def get_deadline_for_next_tour(cls, league_id: int) -> datetime | None:
        current_tour, next_tour = await cls.get_current_and_next_tour(league_id=league_id)

        # Если нет следующего тура, возвращаем ошибку
        if not next_tour:
            raise HTTPException(
                status_code=404,
                detail=f"No next tour found for league with ID {league_id}"
            )

        # Подзапрос для получения минимальной даты матча следующего тура
        tour_start_date = (
            select(func.min(Match.date))
            .join(tour_matches_association, Match.id == tour_matches_association.c.match_id)
            .where(tour_matches_association.c.tour_id == next_tour.id)
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
    async def find_one_by_number(cls, number: int, league_id: int):
        async with async_session_maker() as session:
            stmt = (
                select(cls.model)
                .where(cls.model.number == number, cls.model.league_id == league_id)
                .options(selectinload(cls.model.matches))
            )
            result = await session.execute(stmt)
            tour = result.unique().scalars().first()

            if tour and tour.matches:
                tour.start_date = min(match.date for match in tour.matches)
                tour.end_date = max(match.date for match in tour.matches) + timedelta(hours=2)
                tour.deadline = tour.start_date - timedelta(hours=2)

            return tour

    @classmethod
    async def find_all_with_relations(cls):
        async with async_session_maker() as session:
            stmt = select(cls.model).options(selectinload(cls.model.matches))
            result = await session.execute(stmt)
            tours = result.unique().scalars().all()
            return tours

    @classmethod
    async def find_one_or_none_with_relations(cls, tour_id: int):
        async with async_session_maker() as session:
            stmt = (
                select(cls.model)
                .where(cls.model.id == tour_id)
                .options(selectinload(cls.model.matches))
            )
            result = await session.execute(stmt)
            tour = result.unique().scalars().first()
            return tour

    @classmethod
    async def find_all_by_league(cls, league_id: int) -> list[Tour]:
        async with async_session_maker() as session:
            stmt = (
                select(cls.model)
                .where(cls.model.league_id == league_id)
                .options(selectinload(cls.model.matches))
            )
            result = await session.execute(stmt)
            tours = result.unique().scalars().all()

            for tour in tours:
                if tour.matches:
                    tour.start_date = min(match.date for match in tour.matches)
                    tour.end_date = max(match.date for match in tour.matches) + timedelta(hours=2)
                    tour.deadline = tour.start_date - timedelta(hours=2)

            return tours
