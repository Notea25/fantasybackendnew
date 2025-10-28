from fastapi import HTTPException
import httpx
from app.teams.models import Team
from app.database import async_session_maker
from app.utils.external_api import external_api
from app.config import settings
from app.base_service import BaseService

class TeamService(BaseService):
    model = Team

    @classmethod
    async def add_teams(cls, league_id: int):
        try:
            teams_data = await external_api.fetch_teams(league_id, settings.EXTERNAL_API_SEASON)
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=500, detail=f"External API error: {e}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to fetch teams data: {e}")

        try:
            async with async_session_maker() as session:
                for team_data in teams_data:
                    team = cls.model(**team_data)
                    session.add(team)
                await session.commit()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to add teams to database: {e}")
