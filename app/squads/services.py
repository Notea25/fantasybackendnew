from sqlalchemy.orm import joinedload, selectinload
from sqlalchemy.future import select
from sqlalchemy import delete, insert
from app.squads.models import Squad, squad_players_association, squad_bench_players_association
from app.database import async_session_maker
from app.utils.base_service import BaseService
from app.utils.exceptions import ResourceNotFoundException, FailedOperationException

class SquadService(BaseService):
    model = Squad

    @classmethod
    async def add_player_to_squad(cls, squad_id: int, player_id: int, is_bench: bool = False):
        async with async_session_maker() as session:
            squad = await cls.find_one_or_none(id=squad_id)
            if not squad:
                raise ResourceNotFoundException("Squad not found")

            try:
                if is_bench:
                    stmt = squad_bench_players_association.insert().values(
                        squad_id=squad_id, player_id=player_id
                    )
                else:
                    stmt = squad_players_association.insert().values(
                        squad_id=squad_id, player_id=player_id
                    )
                await session.execute(stmt)
                await session.commit()
            except Exception as e:
                await session.rollback()
                raise FailedOperationException(msg=f"Failed to add player to squad: {e}")

    @classmethod
    async def remove_player_from_squad(cls, squad_id: int, player_id: int, is_bench: bool = False):
        async with async_session_maker() as session:
            squad = await cls.find_one_or_none(id=squad_id)
            if not squad:
                raise ResourceNotFoundException("Squad not found")

            try:
                if is_bench:
                    stmt = delete(squad_bench_players_association).where(
                        squad_bench_players_association.c.squad_id == squad_id,
                        squad_bench_players_association.c.player_id == player_id
                    )
                else:
                    stmt = delete(squad_players_association).where(
                        squad_players_association.c.squad_id == squad_id,
                        squad_players_association.c.player_id == player_id
                    )
                await session.execute(stmt)
                await session.commit()
            except Exception as e:
                await session.rollback()
                raise FailedOperationException(msg=f"Failed to remove player from squad: {e}")

    @classmethod
    async def update_squad_players(cls, squad_id: int, main_player_ids: list[int], bench_player_ids: list[int]):
        async with async_session_maker() as session:
            squad = await cls.find_one_or_none(id=squad_id)
            if not squad:
                raise ResourceNotFoundException("Squad not found")

            try:
                stmt = delete(squad_players_association).where(
                    squad_players_association.c.squad_id == squad_id
                )
                await session.execute(stmt)

                stmt = delete(squad_bench_players_association).where(
                    squad_bench_players_association.c.squad_id == squad_id
                )
                await session.execute(stmt)

                for player_id in main_player_ids:
                    stmt = insert(squad_players_association).values(
                        squad_id=squad_id, player_id=player_id
                    )
                    await session.execute(stmt)

                for player_id in bench_player_ids:
                    stmt = insert(squad_bench_players_association).values(
                        squad_id=squad_id, player_id=player_id
                    )
                    await session.execute(stmt)

                await session.commit()
            except Exception as e:
                await session.rollback()
                raise FailedOperationException(msg=f"Failed to update squad players: {e}")


    @classmethod
    async def find_all_with_relations(cls):
        async with async_session_maker() as session:
            stmt = (
                select(cls.model)
                .options(
                    joinedload(cls.model.user),
                    joinedload(cls.model.league),
                    selectinload(cls.model.players),
                    selectinload(cls.model.bench_players),
                )
            )
            result = await session.execute(stmt)
            squads = result.unique().scalars().all()
            return squads

    @classmethod
    async def find_filtered_with_relations(cls, **filter_by):
        async with async_session_maker() as session:
            stmt = (
                select(cls.model)
                .filter_by(**filter_by)
                .options(
                    joinedload(cls.model.user),
                    joinedload(cls.model.league),
                    selectinload(cls.model.players),
                    selectinload(cls.model.bench_players),
                )
            )
            result = await session.execute(stmt)
            squads = result.unique().scalars().all()
            return squads

    @classmethod
    async def find_one_or_none_with_relations(cls, **filter_by):
        async with async_session_maker() as session:
            stmt = (
                select(cls.model)
                .filter_by(**filter_by)
                .options(
                    joinedload(cls.model.user),
                    joinedload(cls.model.league),
                    selectinload(cls.model.players),
                    selectinload(cls.model.bench_players),
                )
            )
            result = await session.execute(stmt)
            squad = result.unique().scalars().first()
            return squad
