import datetime

from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError
from app.database import async_session_maker
from app.custom_leagues.models import CustomLeague, CustomLeagueType, custom_league_squads
from app.squads.models import Squad
from app.utils.base_service import BaseService
from app.utils.exceptions import ResourceNotFoundException, CustomLeagueException, NotAllowedException

class CustomLeagueService(BaseService):
    model = CustomLeague

    @classmethod
    async def create_custom_league(cls, data: dict, user_id: int):
        async with async_session_maker() as session:
            # Проверяем, что пользователь может создать только 1 USER лигу
            if data.get('type') == CustomLeagueType.USER:
                stmt = select(cls.model).where(
                    cls.model.creator_id == user_id,
                    cls.model.type == CustomLeagueType.USER
                )
                result = await session.execute(stmt)
                existing_league = result.scalars().first()
                if existing_league:
                    raise CustomLeagueException()

            # Администратор может создавать коммерческие и клубные лиги
            if data.get('type') in [CustomLeagueType.COMMERCIAL, CustomLeagueType.CLUB]:
                # В реальном приложении здесь должна быть проверка на админа
                pass

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

            # Только создатель или админ может удалить лигу
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

            # Проверка временных рамок для коммерческих лиг
            if custom_league.type == CustomLeagueType.COMMERCIAL and not custom_league.is_registration_open():
                raise NotAllowedException("Registration for this league is closed")

            stmt = select(Squad).where(Squad.id == squad_id)
            result = await session.execute(stmt)
            squad = result.scalars().first()
            if not squad:
                raise ResourceNotFoundException("Squad not found")

            # Проверка, что сквад не участвует в другой лиге этого же типа
            if custom_league.type == CustomLeagueType.COMMERCIAL:
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
        """
        Получает все коммерческие лиги
        """
        async with async_session_maker() as session:
            stmt = select(cls.model).where(cls.model.type == CustomLeagueType.COMMERCIAL)
            result = await session.execute(stmt)
            return result.scalars().all()

    @classmethod
    async def get_commercial_league_status(cls, league_id: int):
        """Возвращает статус коммерческой лиги с учетом текущего тура"""
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