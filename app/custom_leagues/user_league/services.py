import logging
from typing import List

from sqlalchemy import delete
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
from sqlalchemy.exc import IntegrityError

from app.custom_leagues.user_league.models import UserLeague, user_league_squads
from app.database import async_session_maker
from app.leagues.models import League
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