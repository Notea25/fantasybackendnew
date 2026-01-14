import logging
from typing import Optional, List
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError

from app.custom_leagues.commercial_league.models import CommercialLeague
from app.database import async_session_maker
from app.leagues.models import League
from app.utils.exceptions import ResourceNotFoundException, NotAllowedException


logger = logging.getLogger(__name__)

class CommercialLeagueService:
    @classmethod
    async def create_commercial_league(cls, data: dict) -> CommercialLeague:
        async with async_session_maker() as session:
            try:
                # Проверка существования league_id
                stmt = select(League).where(League.id == data.get("league_id"))
                result = await session.execute(stmt)
                league = result.scalars().first()
                if not league:
                    raise ResourceNotFoundException(f"League with id {data.get('league_id')} not found")

                # Преобразуем datetime в наивный формат, если он содержит tzinfo
                if data.get("registration_start") and data["registration_start"].tzinfo:
                    data["registration_start"] = data["registration_start"].replace(tzinfo=None)
                if data.get("registration_end") and data["registration_end"].tzinfo:
                    data["registration_end"] = data["registration_end"].replace(tzinfo=None)

                # Создание лиги
                commercial_league = CommercialLeague(**data)
                session.add(commercial_league)
                await session.commit()
                return commercial_league

            except IntegrityError as e:
                await session.rollback()
                logger.error(f"Integrity error while creating commercial league: {e}")
                raise NotAllowedException(f"Failed to create commercial league due to integrity error: {e}")
            except Exception as e:
                await session.rollback()
                logger.error(f"Unexpected error while creating commercial league: {e}")
                raise

    @classmethod
    async def get_commercial_leagues(cls, league_id: Optional[int] = None) -> List[CommercialLeague]:
        async with async_session_maker() as session:
            stmt = select(CommercialLeague)
            if league_id:
                stmt = stmt.where(CommercialLeague.league_id == league_id)
            result = await session.execute(stmt)
            return result.scalars().all()
