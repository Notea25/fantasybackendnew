from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from datetime import timedelta
from app.tours.models import Tour
from app.database import async_session_maker
from app.utils.base_service import BaseService

from datetime import datetime, timedelta
from typing import Optional, Tuple

class TourService(BaseService):
    model = Tour

    @classmethod
    async def get_current_and_next_tour(cls) -> Tuple[Optional[Tour], Optional[Tour]]:
        async with async_session_maker() as session:
            stmt = (
                select(cls.model)
                .options(selectinload(cls.model.matches))
            )
            result = await session.execute(stmt)
            tours = result.unique().scalars().all()

            now = datetime.utcnow()
            current_tour = None
            next_tour = None

            for tour in tours:
                if not tour.matches:
                    continue

                tour.start_date = min(match.date for match in tour.matches)
                tour.end_date = max(match.date for match in tour.matches) + timedelta(hours=2)

                if tour.start_date <= now <= tour.end_date:
                    current_tour = tour
                elif tour.start_date > now:
                    if not next_tour or tour.start_date < next_tour.start_date:
                        next_tour = tour

            return current_tour, next_tour

    @classmethod
    async def get_deadline_for_current_tour(cls) -> Optional[datetime]:
        current_tour, _ = await cls.get_current_and_next_tour()
        if current_tour:
            return current_tour.start_date - timedelta(hours=2)
        return None

