from sqlalchemy.orm import joinedload, selectinload
from sqlalchemy.future import select
from app.base_service import BaseService
from app.squads.models import Squad
from app.database import async_session_maker

class SquadService(BaseService):
    model = Squad

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
