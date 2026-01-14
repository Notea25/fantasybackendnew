import logging
from typing import List
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError
from app.database import async_session_maker
from app.leagues.models import League
from app.utils.exceptions import ResourceNotFoundException, NotAllowedException
from app.custom_leagues.user_league.models import UserLeague

logger = logging.getLogger(__name__)

class UserLeagueService:
    @classmethod
    async def create_user_league(cls, data: dict, user_id: int) -> UserLeague:
        async with async_session_maker() as session:
            try:
                # Проверка существования league_id
                stmt = select(League).where(League.id == data.get("league_id"))
                result = await session.execute(stmt)
                league = result.scalars().first()
                if not league:
                    raise ResourceNotFoundException(f"League with id {data.get('league_id')} not found")

                # Проверка на существование лиги у пользователя
                stmt = select(UserLeague).where(
                    UserLeague.creator_id == user_id,
                    UserLeague.league_id == data.get("league_id")
                )
                result = await session.execute(stmt)
                existing_league = result.scalars().first()
                if existing_league:
                    raise NotAllowedException("You already have a league for this competition")

                # Преобразуем datetime в наивный формат, если он содержит tzinfo
                if data.get("registration_start") and data["registration_start"].tzinfo:
                    data["registration_start"] = data["registration_start"].replace(tzinfo=None)
                if data.get("registration_end") and data["registration_end"].tzinfo:
                    data["registration_end"] = data["registration_end"].replace(tzinfo=None)

                # Создание лиги
                user_league = UserLeague(**data, creator_id=user_id)
                session.add(user_league)
                await session.commit()
                return user_league

            except IntegrityError as e:
                await session.rollback()
                logger.error(f"Integrity error while creating user league: {e}")
                raise NotAllowedException(f"Failed to create user league due to integrity error: {e}")
            except Exception as e:
                await session.rollback()
                logger.error(f"Unexpected error while creating user league: {e}")
                raise

    @classmethod
    async def get_user_leagues(cls, user_id: int) -> List[UserLeague]:
        async with async_session_maker() as session:
            stmt = select(UserLeague).where(UserLeague.creator_id == user_id)
            result = await session.execute(stmt)
            return result.scalars().all()
