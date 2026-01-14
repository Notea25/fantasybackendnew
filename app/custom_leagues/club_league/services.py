import logging
from typing import Optional, List, Dict, Any

from sqlalchemy import desc, func
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload

from app.custom_leagues.club_league.models import ClubLeague, club_league_squads
from app.database import async_session_maker
from app.squads.models import Squad, SquadTour
from app.utils.exceptions import ResourceNotFoundException, NotAllowedException

logger = logging.getLogger(__name__)

class ClubLeagueService:

    @classmethod
    async def get_club_leagues(cls, league_id: Optional[int] = None, team_id: Optional[int] = None) -> List[ClubLeague]:
        async with async_session_maker() as session:
            stmt = select(ClubLeague).options(joinedload(ClubLeague.tours), joinedload(ClubLeague.squads))
            if league_id:
                stmt = stmt.where(ClubLeague.league_id == league_id)
            if team_id:
                stmt = stmt.where(ClubLeague.team_id == team_id)
            result = await session.execute(stmt)
            return result.scalars().all()

    @classmethod
    async def get_club_league_by_id(cls, club_league_id: int) -> ClubLeague:
        async with async_session_maker() as session:
            stmt = (
                select(ClubLeague)
                .where(ClubLeague.id == club_league_id)
                .options(joinedload(ClubLeague.tours), joinedload(ClubLeague.squads))
            )
            result = await session.execute(stmt)
            league = result.scalars().first()
            if not league:
                raise ResourceNotFoundException("Club league not found")
            return league

    @classmethod
    async def add_squad_to_club_league(cls, club_league_id: int, squad_id: int, user_id: int) -> ClubLeague:
        async with async_session_maker() as session:
            # Проверка существования клубной лиги
            stmt = select(ClubLeague).where(ClubLeague.id == club_league_id)
            result = await session.execute(stmt)
            club_league = result.scalars().first()
            if not club_league:
                raise ResourceNotFoundException("Club league not found")

            # Проверка существования сквада
            stmt = select(Squad).where(Squad.id == squad_id)
            result = await session.execute(stmt)
            squad = result.scalars().first()
            if not squad:
                raise ResourceNotFoundException("Squad not found")

            # Проверка, что сквад принадлежит пользователю
            if squad.user_id != user_id:
                raise NotAllowedException("You can only add your own squad to a club league")

            # Проверка, что сквад еще не добавлен в эту лигу
            stmt = select(club_league_squads).where(
                club_league_squads.c.club_league_id == club_league_id,
                club_league_squads.c.squad_id == squad_id
            )
            result = await session.execute(stmt)
            if result.first():
                raise NotAllowedException("Squad is already in this club league")

            # Добавление сквада в клубную лигу
            club_league.squads.append(squad)
            await session.commit()
            return club_league

    @classmethod
    async def get_club_league_leaderboard(cls, club_league_id: int, tour_id: int) -> List[Dict[str, Any]]:
        async with async_session_maker() as session:
            # Получаем все сквады, которые участвуют в данной клубной лиге
            stmt = (
                select(club_league_squads.c.squad_id)
                .where(club_league_squads.c.club_league_id == club_league_id)
            )
            result = await session.execute(stmt)
            squad_ids = [row.squad_id for row in result.all()]

            if not squad_ids:
                return []

            # Получаем данные о турах для этих сквадов
            stmt = (
                select(SquadTour)
                .where(
                    SquadTour.squad_id.in_(squad_ids),
                    SquadTour.tour_id == tour_id
                )
                .options(
                    joinedload(SquadTour.squad).joinedload(Squad.user)
                )
                .order_by(desc(SquadTour.points))
            )
            result = await session.execute(stmt)
            squad_tours = result.unique().scalars().all()

            # Получаем общее количество очков для каждого сквада за все туры
            total_points_stmt = (
                select(
                    SquadTour.squad_id,
                    func.sum(SquadTour.points).label("total_points")
                )
                .where(SquadTour.squad_id.in_(squad_ids))
                .group_by(SquadTour.squad_id)
            )
            total_points_result = await session.execute(total_points_stmt)
            total_points = {row.squad_id: row.total_points for row in total_points_result}

            leaderboard = []
            for index, squad_tour in enumerate(squad_tours, start=1):
                squad = squad_tour.squad

                leaderboard.append({
                    "place": index,
                    "squad_id": squad.id,
                    "squad_name": squad.name,
                    "user_id": squad.user.id,
                    "username": squad.user.username,
                    "tour_points": squad_tour.points,
                    "total_points": total_points.get(squad.id, 0),
                })

            return leaderboard