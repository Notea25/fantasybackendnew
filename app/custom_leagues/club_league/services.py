import logging
from typing import Optional, List, Dict, Any

from sqlalchemy import desc, func
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload, selectinload

from app.custom_leagues.club_league.models import ClubLeague, club_league_squads
from app.database import async_session_maker
from app.squads.models import Squad, SquadTour
from app.utils.exceptions import ResourceNotFoundException, NotAllowedException

logger = logging.getLogger(__name__)

class ClubLeagueService:

    @classmethod
    async def get_club_league(cls, league_id: int = None, team_id: int = None):
        async with async_session_maker() as session:
            stmt = select(ClubLeague)
            if league_id:
                stmt = stmt.where(ClubLeague.league_id == league_id)
            if team_id:
                stmt = stmt.where(ClubLeague.team_id == team_id)

            stmt = stmt.options(
                selectinload(ClubLeague.tours),
                selectinload(ClubLeague.squads),
                selectinload(ClubLeague.league),
                selectinload(ClubLeague.team),
            )

            result = await session.execute(stmt)
            club_league = result.unique().scalars().first()
            return club_league

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
            stmt = select(ClubLeague).where(ClubLeague.id == club_league_id)
            result = await session.execute(stmt)
            club_league = result.scalars().first()
            if not club_league:
                raise ResourceNotFoundException("Club league not found")

            stmt = select(Squad).where(Squad.id == squad_id)
            result = await session.execute(stmt)
            squad = result.scalars().first()
            if not squad:
                raise ResourceNotFoundException("Squad not found")

            if squad.user_id != user_id:
                raise NotAllowedException("You can only add your own squad to a club league")

            stmt = select(club_league_squads).where(
                club_league_squads.c.club_league_id == club_league_id,
                club_league_squads.c.squad_id == squad_id
            )
            result = await session.execute(stmt)
            if result.first():
                raise NotAllowedException("Squad is already in this club league")

            club_league.squads.append(squad)
            await session.commit()
            return club_league

    @classmethod
    async def get_club_league_leaderboard(cls, club_league_id: int, tour_id: int) -> List[Dict[str, Any]]:
        async with async_session_maker() as session:
            stmt = (
                select(club_league_squads.c.squad_id)
                .where(club_league_squads.c.club_league_id == club_league_id)
            )
            result = await session.execute(stmt)
            squad_ids = [row.squad_id for row in result.all()]

            if not squad_ids:
                return []

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

            total_points_stmt = (
                select(
                    SquadTour.squad_id,
                    func.sum(SquadTour.points).label("total_points"),
                    func.sum(SquadTour.penalty_points).label("total_penalty_points")
                )
                .where(SquadTour.squad_id.in_(squad_ids))
                .group_by(SquadTour.squad_id)
            )
            total_points_result = await session.execute(total_points_stmt)
            total_points = {row.squad_id: row.total_points for row in total_points_result}
            total_penalty_points = {row.squad_id: row.total_penalty_points for row in total_points_result}

            # Сортируем по чистым очкам
            leaderboard_with_net_points = []
            for squad_tour in squad_tours:
                squad = squad_tour.squad
                total_pts = int(total_points.get(squad.id, 0) or 0)
                total_pen = int(total_penalty_points.get(squad.id, 0) or 0)
                net_points = total_pts - total_pen
                
                leaderboard_with_net_points.append({
                    "squad_tour": squad_tour,
                    "squad": squad,
                    "total_points": total_pts,
                    "penalty_points": total_pen,
                    "net_points": net_points,
                })
            
            leaderboard_with_net_points.sort(key=lambda x: x["net_points"], reverse=True)
            
            leaderboard = []
            for index, entry in enumerate(leaderboard_with_net_points, start=1):
                squad = entry["squad"]
                squad_tour = entry["squad_tour"]
                
                leaderboard.append({
                    "place": index,
                    "squad_id": squad.id,
                    "squad_name": squad.name,
                    "user_id": squad.user.id,
                    "username": squad.user.username,
                    "tour_points": squad_tour.points,
                    "total_points": entry["total_points"],
                    "penalty_points": entry["penalty_points"],
                })

            return leaderboard

    @classmethod
    async def get_club_leagues_by_league_id(cls, league_id: int):
        async with async_session_maker() as session:
            stmt = select(ClubLeague).where(ClubLeague.league_id == league_id)
            result = await session.execute(stmt)
            club_leagues = result.scalars().all()
            return club_leagues

    @classmethod
    async def add_squad_to_club_league_by_team_id(cls, squad_id: int, team_id: int) -> dict:
        async with async_session_maker() as session:
            stmt = select(ClubLeague).where(ClubLeague.team_id == team_id)
            result = await session.execute(stmt)
            club_league = result.scalars().first()
            if not club_league:
                raise ResourceNotFoundException("Club league not found")

            stmt = select(Squad).where(Squad.id == squad_id)
            result = await session.execute(stmt)
            squad = result.scalars().first()
            if not squad:
                raise ResourceNotFoundException("Squad not found")

            stmt = select(club_league_squads).where(
                club_league_squads.c.club_league_id == club_league.id,
                club_league_squads.c.squad_id == squad_id
            )
            result = await session.execute(stmt)
            if result.first():
                raise NotAllowedException("Squad is already in this club league")

            insert_stmt = club_league_squads.insert().values(
                club_league_id=club_league.id,
                squad_id=squad.id
            )
            await session.execute(insert_stmt)
            await session.commit()

            return {"club_league_id": club_league.id, "squad_id": squad.id}

    @classmethod
    async def get_club_league_leaderboard_by_team(cls, team_id: int, tour_id: int) -> List[Dict[str, Any]]:
        async with async_session_maker() as session:
            stmt = select(ClubLeague).where(ClubLeague.team_id == team_id)
            result = await session.execute(stmt)
            club_league = result.scalars().first()
            if not club_league:
                raise ResourceNotFoundException("Club league not found")

            stmt = (
                select(club_league_squads.c.squad_id)
                .where(club_league_squads.c.club_league_id == club_league.id)
            )
            result = await session.execute(stmt)
            squad_ids = [row.squad_id for row in result.all()]

            if not squad_ids:
                return []

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

            total_points_stmt = (
                select(
                    SquadTour.squad_id,
                    func.sum(SquadTour.points).label("total_points"),
                    func.sum(SquadTour.penalty_points).label("total_penalty_points")
                )
                .where(SquadTour.squad_id.in_(squad_ids))
                .group_by(SquadTour.squad_id)
            )
            total_points_result = await session.execute(total_points_stmt)
            total_points = {row.squad_id: row.total_points for row in total_points_result}
            total_penalty_points = {row.squad_id: row.total_penalty_points for row in total_points_result}

            # Сортируем по чистым очкам
            leaderboard_with_net_points = []
            for squad_tour in squad_tours:
                squad = squad_tour.squad
                total_pts = int(total_points.get(squad.id, 0) or 0)
                total_pen = int(total_penalty_points.get(squad.id, 0) or 0)
                net_points = total_pts - total_pen
                
                leaderboard_with_net_points.append({
                    "squad_tour": squad_tour,
                    "squad": squad,
                    "total_points": total_pts,
                    "penalty_points": total_pen,
                    "net_points": net_points,
                })
            
            leaderboard_with_net_points.sort(key=lambda x: x["net_points"], reverse=True)
            
            leaderboard = []
            for index, entry in enumerate(leaderboard_with_net_points, start=1):
                squad = entry["squad"]
                squad_tour = entry["squad_tour"]
                
                leaderboard.append({
                    "place": index,
                    "squad_id": squad.id,
                    "squad_name": squad.name,
                    "user_id": squad.user.id,
                    "username": squad.user.username,
                    "tour_points": squad_tour.points,
                    "total_points": entry["total_points"],
                    "penalty_points": entry["penalty_points"],
                })

            return leaderboard
