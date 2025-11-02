import logging

from sqlalchemy.future import select
from app.teams.models import Team
from app.database import async_session_maker
from app.utils.external_api import external_api
from app.utils.base_service import BaseService
from app.utils.exceptions import ExternalAPIErrorException, FailedOperationException
import httpx

logger = logging.getLogger(__name__)

class TeamService(BaseService):
    model = Team

    @classmethod
    async def add_teams(cls, league_id: int):
        try:
            teams_data = await external_api.fetch_teams(league_id)
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error fetching teams for league {league_id}: {e}")
            raise ExternalAPIErrorException()
        except ValueError as e:
            logger.error(f"No teams found for league {league_id}: {e}")
            raise ExternalAPIErrorException(msg=str(e))
        except Exception as e:
            logger.error(f"Unexpected error fetching teams for league {league_id}: {e}")
            raise ExternalAPIErrorException()

        async with async_session_maker() as session:
            for team_response in teams_data:
                try:
                    team_data = team_response.get("team", {})
                    if not team_data:
                        logger.warning(f"Team data is missing in response: {team_response}")
                        continue

                    stmt = select(Team).where(Team.id == team_data["id"])
                    result = await session.execute(stmt)
                    existing_team = result.scalar_one_or_none()
                    if existing_team:
                        logger.debug(f"Team {team_data['id']} already exists, skipping...")
                        continue

                    team = cls.model(
                        id=team_data["id"],
                        name=team_data["name"],
                        league_id=league_id
                    )
                    session.add(team)
                except KeyError as e:
                    logger.error(f"Missing key in team data: {e}")
                    await session.rollback()
                    raise FailedOperationException(msg=f"Missing key in team data: {e}")
                except Exception as e:
                    logger.error(f"Error processing team {team_data.get('id', 'unknown')}: {e}")
                    await session.rollback()
                    raise FailedOperationException(msg=f"Error processing team: {e}")

            try:
                await session.commit()
            except Exception as e:
                await session.rollback()
                logger.error(f"Failed to commit teams for league {league_id}: {e}")
                raise FailedOperationException(msg=f"Failed to commit teams: {e}")

