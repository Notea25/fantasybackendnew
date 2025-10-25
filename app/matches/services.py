from sqlalchemy import select, or_
from sqlalchemy.orm import selectinload

from app.base_service import BaseService
from app.database import async_session_maker
from app.matches.models import Match

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