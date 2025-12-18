from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from app.tours.models import Tour
from app.database import async_session_maker
from app.utils.base_service import BaseService
from app.utils.exceptions import ResourceNotFoundException

class TourService(BaseService):
    model = Tour

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
    async def find_all_with_relations(cls):
        async with async_session_maker() as session:
            stmt = (
                select(cls.model)
                .options(selectinload(cls.model.matches))
            )
            result = await session.execute(stmt)
            tours = result.unique().scalars().all()
            return tours
