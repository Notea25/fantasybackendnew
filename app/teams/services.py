from sqlalchemy.future import select
from app.teams.models import Team
from app.database import async_session_maker
from app.utils.external_api import external_api
from app.config import settings
from app.base_service import BaseService
from app.exceptions import ExternalAPIErrorException, FailedOperationException
import httpx

class TeamService(BaseService):
    model = Team

    @classmethod
    async def add_teams(cls, league_id: int):
        try:
            teams_data = await external_api.fetch_teams(league_id, settings.EXTERNAL_API_SEASON)
        except httpx.HTTPStatusError:
            raise ExternalAPIErrorException()
        except Exception:
            raise ExternalAPIErrorException()

        async with async_session_maker() as session:
            for team_response in teams_data:
                team_data = team_response["team"]
                stmt = select(Team).where(Team.id == team_data["id"])
                result = await session.execute(stmt)
                existing_team = result.scalar_one_or_none()
                if existing_team:
                    continue

                try:
                    team = cls.model(
                        id=team_data["id"],
                        name=team_data["name"],
                        league_id=league_id
                    )
                    session.add(team)
                except Exception as e:
                    await session.rollback()
                    raise FailedOperationException(msg=f"Failed to add team: {e}")

            try:
                await session.commit()
            except Exception as e:
                await session.rollback()
                raise FailedOperationException(msg=f"Failed to commit teams: {e}")
