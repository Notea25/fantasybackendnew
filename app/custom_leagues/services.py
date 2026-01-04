import datetime

from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload

from app.database import async_session_maker
from app.custom_leagues.models import CustomLeague, custom_league_squads
from app.squads.models import Squad
from app.utils.base_service import BaseService
from app.utils.exceptions import ResourceNotFoundException, CustomLeagueException, NotAllowedException

class CustomLeagueService(BaseService):
    model = CustomLeague

    @classmethod
    async def create_custom_league(cls, data: dict, user_id: int):
        async with async_session_maker() as session:
            if data.get('type') == "USERS":
                stmt = select(cls.model).where(
                    cls.model.creator_id == user_id,
                    cls.model.type == "USERS"
                )
                result = await session.execute(stmt)
                existing_league = result.scalars().first()
                if existing_league:
                    raise CustomLeagueException()

            custom_league = cls.model(**data, creator_id=user_id)
            session.add(custom_league)
            try:
                await session.commit()
            except IntegrityError:
                await session.rollback()
                raise NotAllowedException("Failed to create custom league")
            return custom_league

    @classmethod
    async def delete_custom_league(cls, custom_league_id: int, user_id: int):
        async with async_session_maker() as session:
            stmt = select(cls.model).where(cls.model.id == custom_league_id)
            result = await session.execute(stmt)
            custom_league = result.scalars().first()
            if not custom_league:
                raise ResourceNotFoundException()

            if custom_league.creator_id != user_id:
                raise NotAllowedException("Only creator can delete this league")

            await session.delete(custom_league)
            await session.commit()
            return custom_league


    @classmethod
    async def add_squad_to_custom_league(cls, custom_league_id: int, squad_id: int):
        async with async_session_maker() as session:
            stmt = select(CustomLeague).where(CustomLeague.id == custom_league_id)
            result = await session.execute(stmt)
            custom_league = result.scalars().first()
            if not custom_league:
                raise ResourceNotFoundException("Custom league not found")

            if custom_league.type == "COMMERCIAL" and not custom_league.is_registration_open():
                raise NotAllowedException("Registration for this league is closed")

            stmt = select(Squad).where(Squad.id == squad_id)
            result = await session.execute(stmt)
            squad = result.scalars().first()
            if not squad:
                raise ResourceNotFoundException("Squad not found")

            if custom_league.type == "COMMERCIAL":
                stmt = select(custom_league_squads).where(
                    custom_league_squads.c.squad_id == squad_id,
                    custom_league_squads.c.custom_league_id != custom_league_id
                )
                result = await session.execute(stmt)
                if result.first():
                    raise NotAllowedException("Squad already participates in another commercial league")

            custom_league.squads.append(squad)
            await session.commit()
            return custom_league

    @classmethod
    async def get_all_commercial_leagues(cls):
        async with async_session_maker() as session:
            stmt = select(cls.model).where(cls.model.type == "COMMERCIAL")
            result = await session.execute(stmt)
            return result.scalars().all()

    @classmethod
    async def get_commercial_league_status(cls, league_id: int):
        async with async_session_maker() as session:
            stmt = (
                select(CustomLeague)
                .where(CustomLeague.id == league_id)
                .options(joinedload(CustomLeague.tours))
            )
            result = await session.execute(stmt)
            league = result.scalars().first()

            if not league:
                raise ResourceNotFoundException("League not found")

            return {
                "is_open": league.is_open(),
                "has_current_tour": league.has_current_tour(),
                "is_in_timeframe": league.registration_start <= datetime.now() <= league.registration_end,
                "message": "League is open" if league.is_open() else "League is closed"
        }