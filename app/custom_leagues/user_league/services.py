import logging
from typing import List, Dict, Any

from sqlalchemy import delete, func, desc
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
from sqlalchemy.exc import IntegrityError

from app.custom_leagues.user_league.models import UserLeague, user_league_squads
from app.database import async_session_maker
from app.leagues.models import League
from app.squads.models import SquadTour, Squad
from app.utils.exceptions import ResourceNotFoundException, NotAllowedException


logger = logging.getLogger(__name__)

class UserLeagueService:
    @classmethod
    async def create_user_league(cls, data: dict, user_id: int) -> UserLeague:
        async with async_session_maker() as session:
            try:
                # Проверка существования league_id
                stmt = select(League).where(League.id == data.get("league_id"))
                result = await session.execute(stmt)
                league = result.scalars().first()
                if not league:
                    raise ResourceNotFoundException(f"League with id {data.get('league_id')} not found")

                # Проверка на существование лиги у пользователя
                stmt = select(UserLeague).where(
                    UserLeague.creator_id == user_id,
                    UserLeague.league_id == data.get("league_id")
                )
                result = await session.execute(stmt)
                existing_league = result.scalars().first()
                if existing_league:
                    raise NotAllowedException("You already have a league for this competition")

                # Создание лиги
                user_league = UserLeague(**data, creator_id=user_id)
                session.add(user_league)
                await session.commit()
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
            stmt = select(UserLeague).where(UserLeague.creator_id == user_id).options(
                joinedload(UserLeague.tours),
                joinedload(UserLeague.squads)
            )
            result = await session.execute(stmt)
            return result.scalars().all()

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
            # Проверка существования пользовательской лиги
            stmt = select(UserLeague).where(UserLeague.id == user_league_id)
            result = await session.execute(stmt)
            user_league = result.scalars().first()
            if not user_league:
                raise ResourceNotFoundException("User league not found")

            # Проверка существования сквада
            from app.squads.models import Squad
            stmt = select(Squad).where(Squad.id == squad_id)
            result = await session.execute(stmt)
            squad = result.scalars().first()
            if not squad:
                raise ResourceNotFoundException("Squad not found")

            # Проверка, что сквад принадлежит пользователю
            if squad.user_id != user_id:
                raise NotAllowedException("You can only add your own squad to a user league")

            # Проверка, что сквад еще не добавлен в эту лигу
            stmt = select(user_league_squads).where(
                user_league_squads.c.user_league_id == user_league_id,
                user_league_squads.c.squad_id == squad_id
            )
            result = await session.execute(stmt)
            if result.first():
                raise NotAllowedException("Squad is already in this user league")

            # Добавление сквада в пользовательскую лигу
            user_league.squads.append(squad)
            await session.commit()
            return user_league

    @classmethod
    async def leave_user_league(cls, user_league_id: int, squad_id: int, user_id: int) -> UserLeague:
        async with async_session_maker() as session:
            # Проверка существования пользовательской лиги
            stmt = select(UserLeague).where(UserLeague.id == user_league_id)
            result = await session.execute(stmt)
            user_league = result.scalars().first()
            if not user_league:
                raise ResourceNotFoundException("User league not found")

            # Проверка существования сквада
            from app.squads.models import Squad
            stmt = select(Squad).where(Squad.id == squad_id)
            result = await session.execute(stmt)
            squad = result.scalars().first()
            if not squad:
                raise ResourceNotFoundException("Squad not found")

            # Проверка, что сквад принадлежит пользователю
            if squad.user_id != user_id:
                raise NotAllowedException("You can only remove your own squad from a user league")

            # Удаление сквада из пользовательской лиги
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
            # Проверка существования пользовательской лиги
            stmt = select(UserLeague).where(UserLeague.id == user_league_id)
            result = await session.execute(stmt)
            user_league = result.scalars().first()
            if not user_league:
                raise ResourceNotFoundException("User league not found")

            # Проверка, что пользователь является создателем лиги
            if user_league.creator_id != user_id:
                raise NotAllowedException("Only the creator can delete the user league")

            # Удаление лиги
            await session.delete(user_league)
            await session.commit()

    @classmethod
    async def get_user_league_leaderboard(cls, user_league_id: int, tour_id: int) -> List[Dict[str, Any]]:
        async with async_session_maker() as session:
            # Получаем все сквады, участвующие в данной пользовательской лиге
            stmt = (
                select(user_league_squads.c.squad_id)
                .where(user_league_squads.c.user_league_id == user_league_id)
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
