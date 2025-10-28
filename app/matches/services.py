import httpx
from fastapi import HTTPException
from sqlalchemy import select, or_
from sqlalchemy.orm import selectinload

from app.base_service import BaseService
from app.config import settings
from app.database import async_session_maker
from app.matches.models import Match
from app.utils.external_api import external_api


class MatchService(BaseService):
    model=Match

    @staticmethod
    async def find_matches_by_team(team_id: int) -> list[Match]:
        async with async_session_maker() as session:
            query = (
                select(Match)
                .where(or_(
                    Match.home_team_id == team_id,
                    Match.away_team_id == team_id
                ))
                .options(
                    selectinload(Match.home_team),
                    selectinload(Match.away_team),
                    selectinload(Match.league)
                )
            )
            result = await session.execute(query)
            matches = result.scalars().all()
            return matches

    @staticmethod
    async def add_matches(league_id: int):
        try:
            matches_data = await external_api.fetch_matches(league_id, settings.EXTERNAL_API_SEASON)
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=500, detail=f"External API error: {e}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to fetch matches data: {e}")

        try:
            async with async_session_maker() as session:
                for match_data in matches_data:
                    match = Match(**match_data)
                    session.add(match)
                await session.commit()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to add matches to database: {e}")