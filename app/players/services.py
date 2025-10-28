from fastapi import HTTPException
import httpx
from app.players.models import Player
from app.database import async_session_maker
from app.utils.external_api import external_api
from app.config import settings
from app.base_service import BaseService

class PlayerService(BaseService):
    model = Player

    @classmethod
    async def add_players(cls, team_id: int):
        try:
            players_data = await external_api.fetch_players(team_id, settings.EXTERNAL_API_SEASON)
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=500, detail=f"External API error: {e}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to fetch players data: {e}")

        try:
            async with async_session_maker() as session:
                for player_data in players_data:
                    player = cls.model(**player_data)
                    session.add(player)
                await session.commit()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to add players to database: {e}")
