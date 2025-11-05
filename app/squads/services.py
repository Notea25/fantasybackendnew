from sqlalchemy.orm import joinedload, selectinload
from sqlalchemy.future import select
from sqlalchemy import delete
from app.squads.models import Squad, squad_players_association, squad_bench_players_association
from app.database import async_session_maker
from app.utils.base_service import BaseService
from app.utils.exceptions import ResourceNotFoundException, FailedOperationException
from app.players.services import PlayerService

class SquadService(BaseService):
    model = Squad

    @classmethod
    async def add_player_to_squad(cls, squad_id: int, player_id: int, is_bench: bool = False):
        async with async_session_maker() as session:
            squad = await cls.find_one_or_none(id=squad_id)
            if not squad:
                raise ResourceNotFoundException("Squad not found")

            player = await PlayerService.find_one_or_none(id=player_id)
            if not player:
                raise ResourceNotFoundException("Player not found")

            club_players_count = len([p for p in (squad.players + squad.bench_players) if p.team_id == player.team_id])
            if club_players_count >= 3:
                raise FailedOperationException("Cannot add more than 3 players from the same club")

            if not is_bench and len(squad.players) >= 11:
                raise FailedOperationException("Cannot add more than 11 players to the main squad")
            if is_bench and len(squad.bench_players) >= 4:
                raise FailedOperationException("Cannot add more than 4 players to the bench")

            squad.budget -= player.market_value

            if is_bench:
                stmt = squad_bench_players_association.insert().values(squad_id=squad_id, player_id=player_id)
            else:
                stmt = squad_players_association.insert().values(squad_id=squad_id, player_id=player_id)
            await session.execute(stmt)

            # Пересчёт очков команды
            squad.calculate_points()

            await session.commit()

    @classmethod
    async def remove_player_from_squad(cls, squad_id: int, player_id: int, is_bench: bool = False):
        async with async_session_maker() as session:
            squad = await cls.find_one_or_none(id=squad_id)
            if not squad:
                raise ResourceNotFoundException("Squad not found")

            player = await PlayerService.find_one_or_none(id=player_id)
            if not player:
                raise ResourceNotFoundException("Player not found")

            # Удаление игрока
            if is_bench:
                stmt = delete(squad_bench_players_association).where(
                    squad_bench_players_association.c.squad_id == squad_id,
                    squad_bench_players_association.c.player_id == player_id
                )
                squad.replacements -= 1
            else:
                stmt = delete(squad_players_association).where(
                    squad_players_association.c.squad_id == squad_id,
                    squad_players_association.c.player_id == player_id
                )

            await session.execute(stmt)

            squad.budget += player.market_value

            squad.calculate_points()

            await session.commit()

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
