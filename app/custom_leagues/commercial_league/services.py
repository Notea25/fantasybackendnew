import logging
from typing import Optional, List, Dict, Any

from sqlalchemy import desc
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
from sqlalchemy.exc import IntegrityError

from app.custom_leagues.commercial_league.models import CommercialLeague, commercial_league_squads
from app.database import async_session_maker
from app.leagues.models import League
from app.tours.models import Tour
from app.utils.exceptions import ResourceNotFoundException, NotAllowedException
from app.squads.models import Squad

logger = logging.getLogger(__name__)

class CommercialLeagueService:

    @classmethod
    async def get_commercial_leagues(cls, league_id: int = None):
        async with async_session_maker() as session:
            stmt = select(CommercialLeague)
            if league_id:
                stmt = stmt.where(CommercialLeague.league_id == league_id).options(
                    joinedload(CommercialLeague.tours),
                    joinedload(CommercialLeague.squads),
                    joinedload(CommercialLeague.winner)
                )
            result = await session.execute(stmt)
            leagues = result.unique().scalars().all()

            leagues_with_winner_name = []
            for league in leagues:
                winner_name = league.winner.name if league.winner else None
                leagues_with_winner_name.append({
                    "id": league.id,
                    "name": league.name,
                    "league_id": league.league_id,
                    "prize": league.prize,
                    "logo": league.logo,
                    "winner_id": league.winner_id,
                    "winner_name": winner_name,
                    "registration_start": league.registration_start,
                    "registration_end": league.registration_end,
                    "tours": [{"id": tour.id, "number": tour.number} for tour in league.tours],
                    "squads": [{"squad_id": squad.id, "squad_name": squad.name} for squad in league.squads]
                })

            return leagues_with_winner_name

    @classmethod
    async def get_commercial_league_by_id(cls, commercial_league_id: int) -> CommercialLeague:
        async with async_session_maker() as session:
            stmt = (
                select(CommercialLeague)
                .where(CommercialLeague.id == commercial_league_id)
                .options(
                    joinedload(CommercialLeague.tours),
                    joinedload(CommercialLeague.squads),
                    joinedload(CommercialLeague.winner)
                )
            )
            result = await session.execute(stmt)
            league = result.unique().scalars().first()
            if not league:
                raise ResourceNotFoundException("Commercial league not found")
            return league

    @classmethod
    async def get_commercial_league_leaderboard(cls, commercial_league_id: int, tour_id: int) -> List[Dict[str, Any]]:
        async with async_session_maker() as session:
            stmt = (
                select(commercial_league_squads.c.squad_id)
                .where(commercial_league_squads.c.commercial_league_id == commercial_league_id)
            )
            result = await session.execute(stmt)
            squad_ids = [row.squad_id for row in result.all()]

            if not squad_ids:
                return []

            from app.squads.models import SquadTour, Squad
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

            from sqlalchemy import func
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
                    "total_penalty": total_pen,
                    "tour_penalty": squad_tour.penalty_points,
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
                    # Return tour penalty, not total penalty - frontend needs this to calculate tour_points - penalty
                    "penalty_points": entry["tour_penalty"],
                })

            return leaderboard

    @classmethod
    async def join_commercial_league(cls, squad_id: int, commercial_league_id: int) -> dict:
        async with async_session_maker() as session:
            stmt = select(CommercialLeague).where(CommercialLeague.id == commercial_league_id)
            result = await session.execute(stmt)
            commercial_league = result.scalars().first()
            if not commercial_league:
                raise ResourceNotFoundException("Commercial league not found")

            stmt = select(Squad).where(Squad.id == squad_id)
            result = await session.execute(stmt)
            squad = result.scalars().first()
            if not squad:
                raise ResourceNotFoundException("Squad not found")

            if squad.league_id != commercial_league.league_id:
                raise NotAllowedException("Squad and commercial league must belong to the same league")

            stmt = select(commercial_league_squads).where(
                commercial_league_squads.c.commercial_league_id == commercial_league.id,
                commercial_league_squads.c.squad_id == squad.id
            )
            result = await session.execute(stmt)
            if result.first():
                raise NotAllowedException("Squad is already in this commercial league")

            insert_stmt = commercial_league_squads.insert().values(
                commercial_league_id=commercial_league.id,
                squad_id=squad.id
            )
            await session.execute(insert_stmt)
            await session.commit()

            return {"commercial_league_id": commercial_league.id, "squad_id": squad.id}