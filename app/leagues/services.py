import logging

from sqlalchemy.future import select
from app.leagues.models import League
from app.database import async_session_maker
from app.utils.external_api import external_api
from app.config import settings
from app.utils.base_service import BaseService
from app.utils.exceptions import ExternalAPIErrorException, AlreadyExistsException, FailedOperationException
import httpx

logger = logging.getLogger(__name__)

class LeagueService(BaseService):
    model = League

    @classmethod
    async def add_league(cls, league_id: int):
        try:
            logger.debug(f"Fetching league {league_id} from external API")
            league_data = await external_api.fetch_league(league_id)
            logger.debug(f"League data received: {league_data}")
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error fetching league {league_id}: {e}")
            raise ExternalAPIErrorException()
        except ValueError as e:
            logger.error(f"League {league_id} not found: {e}")
            raise ExternalAPIErrorException(msg=str(e))
        except Exception as e:
            logger.error(f"Unexpected error fetching league {league_id}: {e}")
            raise ExternalAPIErrorException()

        async with async_session_maker() as session:
            stmt = select(League).where(League.id == league_id)
            result = await session.execute(stmt)
            existing_league = result.scalar_one_or_none()
            if existing_league:
                logger.warning(f"League {league_id} already exists")
                raise AlreadyExistsException()

            try:
                # Извлекаем данные из правильной структуры ответа
                league_info = league_data["league"]

                league = cls.model(
                    id=league_info["id"],
                    name=league_info["name"]
                    # sport будет установлен по умолчанию (default=1)
                )
                session.add(league)
                await session.commit()
                await session.refresh(league)
                logger.info(f"League {league_id} added successfully")
                return league
            except Exception as e:
                await session.rollback()
                logger.error(f"Failed to add league {league_id}: {e}")
                raise FailedOperationException(msg=f"Failed to add league: {e}")
