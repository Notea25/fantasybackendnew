import datetime
import logging
from typing import Optional, List, Dict, Any

from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload

from app.custom_leagues.schemas import CustomLeagueSchema
from app.database import async_session_maker
from app.custom_leagues.models import CustomLeague, custom_league_squads
from app.leagues.models import League
from app.squads.models import Squad
from app.utils.base_service import BaseService
from app.utils.exceptions import ResourceNotFoundException, CustomLeagueException, NotAllowedException

logger = logging.getLogger(__name__)

class CustomLeagueService(BaseService):
    model = CustomLeague

    @classmethod
    async def create_custom_league(cls, data: dict, user_id: int):
        async with async_session_maker() as session:
            try:
                # Проверка существования league_id
                stmt = select(League).where(League.id == data.get("league_id"))
                result = await session.execute(stmt)
                league = result.scalars().first()
                if not league:
                    raise ResourceNotFoundException(f"League with id {data.get('league_id')} not found")

                # Проверка на существование лиги типа USERS
                if data.get('type') == "USERS":
                    stmt = select(cls.model).where(
                        cls.model.creator_id == user_id,
                        cls.model.type == "USERS"
                    )
                    result = await session.execute(stmt)
                    existing_league = result.scalars().first()
                    if existing_league:
                        raise CustomLeagueException(
                            "You already have a USER-type league. Only one USER-type league is allowed per user.")

                # Преобразуем datetime в наивный формат, если он содержит tzinfo
                if data.get("registration_start") and data["registration_start"].tzinfo:
                    data["registration_start"] = data["registration_start"].replace(tzinfo=None)
                if data.get("registration_end") and data["registration_end"].tzinfo:
                    data["registration_end"] = data["registration_end"].replace(tzinfo=None)

                # Создание лиги
                custom_league = cls.model(**data, creator_id=user_id)
                session.add(custom_league)
                await session.commit()
                return custom_league

            except IntegrityError as e:
                await session.rollback()
                logger.error(f"Integrity error while creating custom league: {e}")
                raise NotAllowedException(f"Failed to create custom league due to integrity error: {e}")
            except Exception as e:
                await session.rollback()
                logger.error(f"Unexpected error while creating custom league: {e}")
                raise

    @classmethod
    async def delete_custom_league(cls, custom_league_id: int, user_id: int):
        async with async_session_maker() as session:
            stmt = select(cls.model).where(cls.model.id == custom_league_id)
            result = await session.execute(stmt)
            custom_league = result.scalars().first()
            if not custom_league:
                raise ResourceNotFoundException("Custom league not found")

            if custom_league.creator_id != user_id:
                raise NotAllowedException("Only creator can delete this league")

            await session.delete(custom_league)
            await session.commit()
            return custom_league

    @classmethod
    async def get_all_commercial_leagues(cls, league_id: Optional[int] = None) -> List[CustomLeague]:
        async with async_session_maker() as session:
            stmt = (
                select(CustomLeague)
                .where(CustomLeague.type == "COMMERCIAL")
                .options(joinedload(CustomLeague.tours))
            )
            if league_id:
                stmt = stmt.where(CustomLeague.league_id == league_id)
            result = await session.execute(stmt)
            return result.scalars().all()

    @classmethod
    async def get_commercial_league_status(cls, league_id: int) -> Dict[str, Any]:
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

            now = datetime.datetime.now()
            is_open = league.registration_start <= now <= league.registration_end if league.registration_start and league.registration_end else False

            return {
                "id": league.id,
                "name": league.name,
                "is_open": is_open,
                "has_current_tour": bool(league.tours),
                "tours": [{"id": tour.id, "name": tour.name} for tour in league.tours],
                "registration_start": league.registration_start,
                "registration_end": league.registration_end,
                "message": "League is open" if is_open else "League is closed"
            }

    @classmethod
    async def get_club_league(cls, custom_league_id: int) -> Optional[CustomLeague]:
        async with async_session_maker() as session:
            stmt = (
                select(CustomLeague)
                .where(CustomLeague.id == custom_league_id)
                .options(joinedload(CustomLeague.team), joinedload(CustomLeague.tours))
            )
            result = await session.execute(stmt)
            return result.scalars().first()

    @classmethod
    async def get_all_custom_leagues(cls) -> List[CustomLeague]:
        async with async_session_maker() as session:
            stmt = (
                select(CustomLeague)
                .options(joinedload(CustomLeague.tours))
            )
            result = await session.execute(stmt)
            return result.scalars().all()

    @classmethod
    async def add_squad_to_custom_league(cls, custom_league_id: int, squad_id: int, user_id: int) -> CustomLeague:
        async with async_session_maker() as session:
            # Проверка существования кастомной лиги
            stmt = select(CustomLeague).where(CustomLeague.id == custom_league_id)
            result = await session.execute(stmt)
            custom_league = result.scalars().first()
            if not custom_league:
                raise ResourceNotFoundException("Custom league not found")

            # Проверка существования сквада
            stmt = select(Squad).where(Squad.id == squad_id)
            result = await session.execute(stmt)
            squad = result.scalars().first()
            if not squad:
                raise ResourceNotFoundException("Squad not found")

            # Проверка, что сквад принадлежит пользователю
            if squad.user_id != user_id:
                raise NotAllowedException("You can only add your own squad to a custom league")

            # Проверка, что сквад еще не добавлен в эту лигу
            stmt = select(custom_league_squads).where(
                custom_league_squads.c.custom_league_id == custom_league_id,
                custom_league_squads.c.squad_id == squad_id
            )
            result = await session.execute(stmt)
            if result.first():
                raise NotAllowedException("Squad is already in this custom league")

            # Добавление сквада в кастомную лигу
            custom_league.squads.append(squad)
            await session.commit()
            return custom_league

    @classmethod
    async def get_custom_leagues_by_league_id(cls, league_id: int) -> List[CustomLeague]:
        async with async_session_maker() as session:
            stmt = (
                select(CustomLeague)
                .where(CustomLeague.league_id == league_id)
                .options(joinedload(CustomLeague.tours))
            )
            result = await session.execute(stmt)
            return result.scalars().all()

    @classmethod
    async def get_custom_leagues_by_type(cls, league_type: str) -> List[CustomLeague]:
        async with async_session_maker() as session:
            stmt = (
                select(CustomLeague)
                .where(CustomLeague.type == league_type)
                .options(joinedload(CustomLeague.tours))
            )
            result = await session.execute(stmt)
            return result.scalars().all()

    @classmethod
    async def get_club_custom_league_by_team_id(cls, team_id: int) -> Optional[CustomLeague]:
        async with async_session_maker() as session:
            stmt = (
                select(CustomLeague)
                .where(CustomLeague.team_id == team_id, CustomLeague.type == "Club")
                .options(joinedload(CustomLeague.tours))
            )
            result = await session.execute(stmt)
            return result.scalars().first()
