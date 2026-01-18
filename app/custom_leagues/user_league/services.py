import logging
from typing import List, Dict, Any
from sqlalchemy import select, func, delete, desc
from sqlalchemy.orm import joinedload
from sqlalchemy.exc import IntegrityError

from app.custom_leagues.user_league.schemas import UserLeagueWithStatsSchema
from app.database import async_session_maker
from app.custom_leagues.user_league.models import UserLeague, user_league_squads
from app.leagues.models import League
from app.squads.models import Squad, SquadTour
from app.tours.models import Tour, user_league_tours
from app.utils.exceptions import ResourceNotFoundException, NotAllowedException

logger = logging.getLogger(__name__)

class UserLeagueService:

    @classmethod
    async def create_user_league(cls, data: dict, user_id: int) -> UserLeague:
        async with async_session_maker() as session:
            try:
                stmt = select(League).where(League.id == data.get("league_id"))
                result = await session.execute(stmt)
                league = result.scalars().first()
                if not league:
                    raise ResourceNotFoundException(f"League with id {data.get('league_id')} not found")

                user_league = UserLeague(**data, creator_id=user_id)
                session.add(user_league)
                await session.commit()

                stmt = select(Tour).where(Tour.league_id == data.get("league_id"))
                result = await session.execute(stmt)
                tours = result.scalars().all()

                for tour in tours:
                    insert_stmt = user_league_tours.insert().values(
                        user_league_id=user_league.id,
                        tour_id=tour.id
                    )
                    await session.execute(insert_stmt)

                stmt = select(Squad).where(Squad.user_id == user_id, Squad.league_id == data.get("league_id"))
                result = await session.execute(stmt)
                squad = result.scalars().first()

                if squad:
                    stmt = select(user_league_squads).where(
                        user_league_squads.c.user_league_id == user_league.id,
                        user_league_squads.c.squad_id == squad.id
                    )
                    result = await session.execute(stmt)
                    if not result.first():
                        insert_stmt = user_league_squads.insert().values(
                            user_league_id=user_league.id,
                            squad_id=squad.id
                        )
                        await session.execute(insert_stmt)

                await session.commit()

                stmt = (
                    select(UserLeague)
                    .where(UserLeague.id == user_league.id)
                    .options(joinedload(UserLeague.tours), joinedload(UserLeague.squads))
                )
                result = await session.execute(stmt)
                user_league = result.unique().scalars().first()

                return user_league

            except IntegrityError as e:
                await session.rollback()
                logger.error(f"Integrity error while creating user league: {e}")
                raise NotAllowedException(f"Failed to create user league due to integrity error: {e}")
            except Exception as e:
                await session.rollback()
                logger.error(f"Unexpected error while creating user league: {e}")
                raise

    @classmethod
    async def get_user_leagues(cls, user_id: int) -> List[UserLeague]:
        async with async_session_maker() as session:
            stmt = (
                select(UserLeague)
                .where(UserLeague.creator_id == user_id)
                .options(joinedload(UserLeague.tours), joinedload(UserLeague.squads))
            )
            result = await session.execute(stmt)
            return result.unique().scalars().all()

    @classmethod
    async def get_user_league_by_id(cls, user_league_id: int) -> UserLeague:
        async with async_session_maker() as session:
            stmt = (
                select(UserLeague)
                .where(UserLeague.id == user_league_id)
                .options(joinedload(UserLeague.tours), joinedload(UserLeague.squads))
            )
            result = await session.execute(stmt)
            league = result.scalars().first()
            if not league:
                raise ResourceNotFoundException("User league not found")
            return league

    @classmethod
    async def join_user_league(cls, user_league_id: int, squad_id: int, user_id: int) -> UserLeague:
        async with async_session_maker() as session:
            try:
                stmt = select(UserLeague).where(UserLeague.id == user_league_id)
                result = await session.execute(stmt)
                user_league = result.scalars().first()
                if not user_league:
                    raise ResourceNotFoundException("User league not found")

                stmt = select(Squad).where(Squad.id == squad_id)
                result = await session.execute(stmt)
                squad = result.scalars().first()
                if not squad:
                    raise ResourceNotFoundException("Squad not found")

                if squad.user_id != user_id:
                    raise NotAllowedException("You can only add your own squad to a user league")

                stmt = select(user_league_squads).where(
                    user_league_squads.c.user_league_id == user_league_id,
                    user_league_squads.c.squad_id == squad_id
                )
                result = await session.execute(stmt)
                if result.first():
                    raise NotAllowedException("Squad is already in this user league")

                insert_stmt = user_league_squads.insert().values(
                    user_league_id=user_league_id,
                    squad_id=squad_id
                )
                await session.execute(insert_stmt)
                await session.commit()

                await session.refresh(user_league)
                return user_league

            except Exception as e:
                await session.rollback()
                logger.error(f"Error while joining user league: {e}")
                raise

    @classmethod
    async def leave_user_league(cls, user_league_id: int, squad_id: int, user_id: int) -> UserLeague:
        async with async_session_maker() as session:
            stmt = select(UserLeague).where(UserLeague.id == user_league_id)
            result = await session.execute(stmt)
            user_league = result.scalars().first()
            if not user_league:
                raise ResourceNotFoundException("User league not found")

            stmt = select(Squad).where(Squad.id == squad_id)
            result = await session.execute(stmt)
            squad = result.scalars().first()
            if not squad:
                raise ResourceNotFoundException("Squad not found")

            if squad.user_id != user_id:
                raise NotAllowedException("You can only remove your own squad from a user league")

            stmt = delete(user_league_squads).where(
                user_league_squads.c.user_league_id == user_league_id,
                user_league_squads.c.squad_id == squad_id
            )
            await session.execute(stmt)
            await session.commit()
            return user_league

    @classmethod
    async def delete_user_league(cls, user_league_id: int, user_id: int):
        async with async_session_maker() as session:
            stmt = select(UserLeague).where(UserLeague.id == user_league_id)
            result = await session.execute(stmt)
            user_league = result.scalars().first()
            if not user_league:
                raise ResourceNotFoundException("User league not found")

            if user_league.creator_id != user_id:
                raise NotAllowedException("Only the creator can delete the user league")

            await session.delete(user_league)
            await session.commit()

    @classmethod
    async def get_my_squad_leagues(cls, user_id: int) -> List[UserLeagueWithStatsSchema]:
        async with async_session_maker() as session:
            try:
                leagues_data = []

                stmt = select(Squad).where(Squad.user_id == user_id)
                result = await session.execute(stmt)
                squads = result.unique().scalars().all()

                for squad in squads:
                    stmt = (
                        select(user_league_squads.c.user_league_id)
                        .where(user_league_squads.c.squad_id == squad.id)
                    )
                    result = await session.execute(stmt)
                    user_league_ids = [row.user_league_id for row in result.unique().all()]

                    for user_league_id in user_league_ids:
                        stmt = (
                            select(UserLeague)
                            .where(UserLeague.id == user_league_id)
                            .options(joinedload(UserLeague.league))
                        )
                        result = await session.execute(stmt)
                        user_league = result.unique().scalars().first()

                        if not user_league:
                            continue

                        stmt = (
                            select(user_league_squads.c.squad_id)
                            .where(user_league_squads.c.user_league_id == user_league_id)
                        )
                        result = await session.execute(stmt)
                        squad_ids_in_league = [row.squad_id for row in result.unique().all()]

                        stmt = (
                            select(SquadTour.squad_id, func.sum(SquadTour.points).label("total_points"))
                            .where(SquadTour.squad_id.in_(squad_ids_in_league))
                            .group_by(SquadTour.squad_id)
                        )
                        result = await session.execute(stmt)
                        squad_points = {row.squad_id: row.total_points for row in result.unique().all()}

                        sorted_squads = sorted(squad_points.items(), key=lambda x: x[1], reverse=True)
                        squad_place = next((i + 1 for i, (s_id, _) in enumerate(sorted_squads) if s_id == squad.id),
                                           len(squad_ids_in_league))

                        leagues_data.append(
                            UserLeagueWithStatsSchema(
                                user_league_id=user_league.id,
                                user_league_name=user_league.name,
                                total_players=len(squad_ids_in_league),
                                squad_place=squad_place,
                                is_creator=user_league.creator_id == user_id,
                                squad_id=squad.id,
                                squad_name=squad.name,
                            )
                        )

                return leagues_data

            except Exception as e:
                logger.error(f"Error in get_my_squad_leagues: {e}")
                raise

    @classmethod
    async def get_user_league_leaderboard(cls, user_league_id: int, tour_id: int) -> List[Dict[str, Any]]:
        async with async_session_maker() as session:
            stmt = (
                select(user_league_squads.c.squad_id)
                .where(user_league_squads.c.user_league_id == user_league_id)
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