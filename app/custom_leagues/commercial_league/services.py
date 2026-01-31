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
from app.squad_tours.models import SquadTour
from app.squads.services import SquadService, SquadPoints

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
            
            # Get squads with user data
            squads_stmt = (
                select(Squad)
                .where(Squad.id.in_(squad_ids))
                .options(joinedload(Squad.user))
            )
            squads_result = await session.execute(squads_stmt)
            squads = squads_result.unique().scalars().all()
            
            # Calculate all points using the helper function
            points_map = await SquadService.calculate_squad_points_bulk(session, squad_ids, tour_id)

            # Сортируем по чистым очкам
            leaderboard_with_net_points = []
            for squad in squads:
                points = points_map.get(squad.id, SquadPoints(0, 0, 0, 0, 0, 0))
                
                leaderboard_with_net_points.append({
                    "squad": squad,
                    "points": points,
                })
            
            leaderboard_with_net_points.sort(key=lambda x: x["points"].total_net, reverse=True)
            
            leaderboard = []
            for index, entry in enumerate(leaderboard_with_net_points, start=1):
                squad = entry["squad"]
                points = entry["points"]
                
                leaderboard.append({
                    "place": index,
                    "squad_id": squad.id,
                    "squad_name": squad.name,
                    "user_id": squad.user.id,
                    "username": squad.user.username,
                    "tour_points": points.tour_net,
                    "total_points": points.total_earned,
                    # Return tour penalty for current tour display
                    "penalty_points": points.tour_penalty,
                    # Return total penalties for "Всего" column calculation
                    "total_penalty_points": points.total_penalty,
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