from sqlalchemy.future import select
from app.leagues.models import League
from app.database import async_session_maker
from app.utils.external_api import external_api
from app.config import settings
from app.utils.base_service import BaseService
from app.utils.exceptions import ExternalAPIErrorException, AlreadyExistsException, FailedOperationException
import httpx

class LeagueService(BaseService):
    model = League

    @classmethod
    async def add_league(cls, league_id: int):
        try:
            league_data = await external_api.fetch_league(league_id, settings.EXTERNAL_API_SEASON)
        except httpx.HTTPStatusError:
            raise ExternalAPIErrorException()
        except ValueError:
            raise ExternalAPIErrorException(msg="League not found")
        except Exception:
            raise ExternalAPIErrorException()

        async with async_session_maker() as session:
            stmt = select(League).where(League.id == league_id)
            result = await session.execute(stmt)
            existing_league = result.scalar_one_or_none()
            if existing_league:
                raise AlreadyExistsException()

            try:
                league = cls.model(id=league_data["id"], name=league_data["name"])
                session.add(league)
                await session.commit()
                await session.refresh(league)
                return league
            except Exception as e:
                await session.rollback()
                raise FailedOperationException(msg=f"Failed to add league: {e}")
