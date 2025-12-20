from sqlalchemy.future import select
from app.database import async_session_maker
from app.custom_leagues.models import CustomLeague, CustomLeagueType

from app.squads.models import Squad
from app.tours.models import Tour
from app.utils.base_service import BaseService
from app.utils.exceptions import ResourceNotFoundException

class CustomLeagueService(BaseService):
    model = CustomLeague

    @classmethod
    async def create_custom_league(cls, data: dict):
        async with async_session_maker() as session:
            custom_league = cls.model(**data)
            session.add(custom_league)
            await session.commit()
            return custom_league

    @classmethod
    async def get_by_id(cls, custom_league_id: int):
        async with async_session_maker() as session:
            stmt = select(cls.model).where(cls.model.id == custom_league_id)
            result = await session.execute(stmt)
            custom_league = result.scalars().first()
            if not custom_league:
                raise ResourceNotFoundException()
            return custom_league

    @classmethod
    async def add_tour(cls, custom_league_id: int, tour_id: int):
        async with async_session_maker() as session:
            custom_league = await cls.get_by_id(custom_league_id)
            stmt = select(Tour).where(Tour.id == tour_id)
            result = await session.execute(stmt)
            tour = result.scalars().first()
            if not tour:
                raise ResourceNotFoundException("Tour not found")

            custom_league.tours.append(tour)
            await session.commit()
            return custom_league

    @classmethod
    async def add_squad(cls, custom_league_id: int, squad_id: int):
        async with async_session_maker() as session:
            custom_league = await cls.get_by_id(custom_league_id)
            stmt = select(Squad).where(Squad.id == squad_id)
            result = await session.execute(stmt)
            squad = result.scalars().first()
            if not squad:
                raise ResourceNotFoundException("Squad not found")

            custom_league.squads.append(squad)
            await session.commit()
            return custom_league
