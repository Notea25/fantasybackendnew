from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload
from sqlalchemy.future import select
from sqlalchemy import delete

from app.players.models import Player
from app.squads.models import Squad, squad_players_association, squad_bench_players_association
from app.database import async_session_maker
from app.utils.base_service import BaseService
from app.utils.exceptions import ResourceNotFoundException, FailedOperationException
from app.players.services import PlayerService

class SquadService(BaseService):
    model = Squad

    @classmethod
    async def create_squad(cls, name: str, user_id: int, league_id: int):
        async with async_session_maker() as session:
            squad = cls.model(name=name, user_id=user_id, league_id=league_id)
            session.add(squad)
            await session.commit()
            await session.refresh(squad)
            return squad

    @classmethod
    async def add_player_to_squad(cls, squad_id: int, player_id: int, is_bench: bool = False):
        async with async_session_maker() as session:
            squad = await session.execute(
                select(cls.model)
                .where(cls.model.id == squad_id)
                .options(
                    selectinload(cls.model.players),
                    selectinload(cls.model.bench_players),
                )
            )
            squad = squad.scalars().first()
            if not squad:
                raise ResourceNotFoundException("Squad not found")

            player = await session.get(PlayerService.model, player_id)
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
            await session.commit()

            # Обновляем объект squad после коммита
            await session.refresh(squad)
            return squad

    @classmethod
    async def remove_player_from_squad(cls, squad_id: int, player_id: int, is_bench: bool = False):
        async with async_session_maker() as session:
            squad = await session.execute(
                select(cls.model)
                .where(cls.model.id == squad_id)
                .options(
                    selectinload(cls.model.players),
                    selectinload(cls.model.bench_players),
                )
            )
            squad = squad.scalars().first()
            if not squad:
                raise ResourceNotFoundException("Squad not found")

            player = await session.get(PlayerService.model, player_id)
            if not player:
                raise ResourceNotFoundException("Player not found")

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

            # Обновляем объект squad после коммита
            await session.refresh(squad)
            return squad

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
                    selectinload(cls.model.players).joinedload(Player.stats),
                    selectinload(cls.model.bench_players).joinedload(Player.stats),
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
                    selectinload(cls.model.players).selectinload(Player.stats),
                    selectinload(cls.model.bench_players).selectinload(Player.stats),
                )
            )
            result = await session.execute(stmt)
            squad = result.unique().scalars().first()
            return squad
