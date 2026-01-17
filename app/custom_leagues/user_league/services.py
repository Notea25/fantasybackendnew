import logging
from typing import List
from sqlalchemy import select, func, delete
from sqlalchemy.orm import joinedload
from sqlalchemy.exc import IntegrityError

from app.custom_leagues.user_league.schemas import UserLeagueWithStatsSchema
from app.database import async_session_maker
from app.custom_leagues.user_league.models import UserLeague, user_league_squads
from app.leagues.models import League
from app.squads.models import Squad, SquadTour
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
    async def get_my_squad_leagues(cls, user_id: int) -> List[UserLeagueWithStatsSchema]:
        async with async_session_maker() as session:
            # 1. Получаем все сквады текущего пользователя
            stmt = select(Squad).where(Squad.user_id == user_id)
            result = await session.execute(stmt)
            squads = result.scalars().all()

            leagues_data = []
            for squad in squads:
                # 2. Получаем все пользовательские лиги, в которых участвует сквад
                stmt = (
                    select(user_league_squads.c.user_league_id)
                    .where(user_league_squads.c.squad_id == squad.id)
                )
                result = await session.execute(stmt)
                user_league_ids = [row.user_league_id for row in result.all()]

                for user_league_id in user_league_ids:
                    # 3. Получаем информацию о лиге
                    stmt = (
                        select(UserLeague)
                        .where(UserLeague.id == user_league_id)
                        .options(joinedload(UserLeague.league))
                    )
                    result = await session.execute(stmt)
                    user_league = result.scalars().first()

                    # 4. Получаем всех сквадов в лиге
                    stmt = (
                        select(user_league_squads.c.squad_id)
                        .where(user_league_squads.c.user_league_id == user_league_id)
                    )
                    result = await session.execute(stmt)
                    squad_ids_in_league = [row.squad_id for row in result.all()]

                    # 5. Получаем очки всех сквадов в лиге
                    stmt = (
                        select(SquadTour.squad_id, func.sum(SquadTour.points).label("total_points"))
                        .where(SquadTour.squad_id.in_(squad_ids_in_league))
                        .group_by(SquadTour.squad_id)
                    )
                    result = await session.execute(stmt)
                    squad_points = {row.squad_id: row.total_points for row in result.all()}

                    # 6. Сортируем сквады по очкам
                    sorted_squads = sorted(squad_points.items(), key=lambda x: x[1], reverse=True)
                    squad_place = next((i + 1 for i, (s_id, _) in enumerate(sorted_squads) if s_id == squad.id), len(squad_ids_in_league))

                    # 7. Формируем ответ
                    leagues_data.append(
                        UserLeagueWithStatsSchema(
                            user_league_id=user_league.id,
                            league_name=user_league.league.name,
                            total_players=len(squad_ids_in_league),
                            squad_place=squad_place,
                            is_creator=user_league.creator_id == user_id,
                            squad_id=squad.id,
                            squad_name=squad.name,
                        )
                    )

            return leagues_data
