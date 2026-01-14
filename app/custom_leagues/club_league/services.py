import logging
from typing import Optional, List
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError

from app.custom_leagues.club_league.models import ClubLeague
from app.database import async_session_maker
from app.leagues.models import League
from app.teams.models import Team
from app.utils.exceptions import ResourceNotFoundException, NotAllowedException


logger = logging.getLogger(__name__)

class ClubLeagueService:
    @classmethod
    async def create_club_league(cls, data: dict) -> ClubLeague:
        async with async_session_maker() as session:
            try:
                # Проверка существования league_id
                stmt = select(League).where(League.id == data.get("league_id"))
                result = await session.execute(stmt)
                league = result.scalars().first()
                if not league:
                    raise ResourceNotFoundException(f"League with id {data.get('league_id')} not found")

                # Проверка существования team_id
                stmt = select(Team).where(Team.id == data.get("team_id"))
                result = await session.execute(stmt)
                team = result.scalars().first()
                if not team:
                    raise ResourceNotFoundException(f"Team with id {data.get('team_id')} not found")

                # Преобразуем datetime в наивный формат, если он содержит tzinfo
                if data.get("registration_start") and data["registration_start"].tzinfo:
                    data["registration_start"] = data["registration_start"].replace(tzinfo=None)
                if data.get("registration_end") and data["registration_end"].tzinfo:
                    data["registration_end"] = data["registration_end"].replace(tzinfo=None)

                # Создание лиги
                club_league = ClubLeague(**data)
                session.add(club_league)
                await session.commit()
                return club_league

            except IntegrityError as e:
                await session.rollback()
                logger.error(f"Integrity error while creating club league: {e}")
                raise NotAllowedException(f"Failed to create club league due to integrity error: {e}")
            except Exception as e:
                await session.rollback()
                logger.error(f"Unexpected error while creating club league: {e}")
                raise

    @classmethod
    async def get_club_leagues(cls, league_id: Optional[int] = None, team_id: Optional[int] = None) -> List[ClubLeague]:
        async with async_session_maker() as session:
            stmt = select(ClubLeague)
            if league_id:
                stmt = stmt.where(ClubLeague.league_id == league_id)
            if team_id:
                stmt = stmt.where(ClubLeague.team_id == team_id)
            result = await session.execute(stmt)
            return result.scalars().all()
