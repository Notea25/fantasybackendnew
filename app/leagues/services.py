from app.leagues.models import League
from app.database import async_session_maker
from app.utils.external_api import external_api
from app.config import settings
from app.base_service import BaseService
from app.exceptions import ExternalAPIErrorException, LeagueNotFoundException, FailedToAddLeagueException
import httpx

class LeagueService(BaseService):
    model = League

    @classmethod
    async def add_league(cls, league_id: int):
        try:
            league_data = await external_api.fetch_league(league_id, settings.EXTERNAL_API_SEASON)
        except httpx.HTTPStatusError as e:
            raise ExternalAPIErrorException()
        except ValueError:
            raise LeagueNotFoundException()
        except Exception:
            raise ExternalAPIErrorException()

        try:
            async with async_session_maker() as session:
                league = cls.model(id=league_data["id"], name=league_data["name"])
                session.add(league)
                await session.commit()
                await session.refresh(league)
                return league
        except Exception:
            raise FailedToAddLeagueException()
