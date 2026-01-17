import logging
from typing import Optional, List, Dict, Any

from sqlalchemy import desc
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
from sqlalchemy.exc import IntegrityError

from app.custom_leagues.commercial_league.models import CommercialLeague, commercial_league_squads
from app.database import async_session_maker
from app.leagues.models import League
from app.utils.exceptions import ResourceNotFoundException, NotAllowedException

from app.squads.models import Squad

logger = logging.getLogger(__name__)

class CommercialLeagueService:

    @classmethod
    async def get_commercial_leagues(cls, league_id: int = None):
        async with async_session_maker() as session:
            stmt = select(CommercialLeague)
            if league_id:
                stmt = stmt.where(CommercialLeague.league_id == league_id)

            # Не используем joinedload для коллекций
            result = await session.execute(stmt)
            commercial_leagues = result.unique().scalars().all()
            return commercial_leagues

    @classmethod
    async def get_commercial_league_by_id(cls, commercial_league_id: int) -> CommercialLeague:
        async with async_session_maker() as session:
            stmt = (
                select(CommercialLeague)
                .where(CommercialLeague.id == commercial_league_id)
                .options(joinedload(CommercialLeague.tours), joinedload(CommercialLeague.squads))
            )
            result = await session.execute(stmt)
            league = result.scalars().first()
            if not league:
                raise ResourceNotFoundException("Commercial league not found")
            return league


    @classmethod
    async def get_commercial_league_leaderboard(cls, commercial_league_id: int, tour_id: int) -> List[Dict[str, Any]]:
        async with async_session_maker() as session:
            # Получаем все сквады, которые участвуют в данной коммерческой лиге
            stmt = (
                select(commercial_league_squads.c.squad_id)
                .where(commercial_league_squads.c.commercial_league_id == commercial_league_id)
            )
            result = await session.execute(stmt)
            squad_ids = [row.squad_id for row in result.all()]

            if not squad_ids:
                return []

            # Получаем данные о турах для этих сквадов
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

            # Получаем общее количество очков для каждого сквада за все туры
            from sqlalchemy import func
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

    @classmethod
    async def join_commercial_league(cls, squad_id: int, commercial_league_id: int) -> dict:
        async with async_session_maker() as session:
            # Проверка существования коммерческой лиги
            stmt = select(CommercialLeague).where(CommercialLeague.id == commercial_league_id)
            result = await session.execute(stmt)
            commercial_league = result.scalars().first()
            if not commercial_league:
                raise ResourceNotFoundException("Commercial league not found")

            # Проверка существования сквада
            stmt = select(Squad).where(Squad.id == squad_id)
            result = await session.execute(stmt)
            squad = result.scalars().first()
            if not squad:
                raise ResourceNotFoundException("Squad not found")

            # Проверка, что сквад и коммерческая лига принадлежат одной и той же лиге
            if squad.league_id != commercial_league.league_id:
                raise NotAllowedException("Squad and commercial league must belong to the same league")

            # Проверка, что сквад еще не добавлен в эту лигу
            stmt = select(commercial_league_squads).where(
                commercial_league_squads.c.commercial_league_id == commercial_league.id,
                commercial_league_squads.c.squad_id == squad.id
            )
            result = await session.execute(stmt)
            if result.first():
                raise NotAllowedException("Squad is already in this commercial league")

            # Добавление записи в промежуточную таблицу
            insert_stmt = commercial_league_squads.insert().values(
                commercial_league_id=commercial_league.id,
                squad_id=squad.id
            )
            await session.execute(insert_stmt)
            await session.commit()

            return {"commercial_league_id": commercial_league.id, "squad_id": squad.id}