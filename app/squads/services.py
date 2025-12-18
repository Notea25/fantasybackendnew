from sqlalchemy.orm import joinedload, selectinload
from sqlalchemy.future import select
from sqlalchemy import delete

from app.players.models import Player
from app.squads.models import Squad, squad_players_association, squad_bench_players_association
from app.database import async_session_maker
from app.utils.base_service import BaseService
from app.utils.exceptions import ResourceNotFoundException, FailedOperationException

class SquadService(BaseService):
    model = Squad

    @classmethod
    async def create_squad(cls, name: str, user_id: int, league_id: int, fav_team_id: int):
        async with async_session_maker() as session:

            existing_squad = await session.execute(
                select(cls.model)
                .where(cls.model.user_id == user_id, cls.model.league_id == league_id)
            )
            existing_squad = existing_squad.scalars().first()

            if existing_squad:
                raise FailedOperationException("User already has a squad in this league")

            squad = cls.model(name=name, user_id=user_id, league_id=league_id, fav_team_id=fav_team_id)
            session.add(squad)
            await session.commit()
            await session.refresh(squad)
            return squad

    @classmethod
    async def update_squad_players(cls, squad_id: int, main_player_ids: list[int], bench_player_ids: list[int]):
        async with async_session_maker() as session:
            # Получаем сквад с текущими игроками
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

            players = await session.execute(select(Player).where(Player.id.in_(main_player_ids + bench_player_ids)))
            players = players.scalars().all()
            player_by_id = {player.id: player for player in players}

            if len(players) != len(main_player_ids) + len(bench_player_ids):
                raise ResourceNotFoundException("One or more players not found")

            club_counts = {}
            for player_id in main_player_ids + bench_player_ids:
                player = player_by_id[player_id]
                club_counts[player.team_id] = club_counts.get(player.team_id, 0) + 1
                if club_counts[player.team_id] > 3:
                    raise FailedOperationException("Cannot add more than 3 players from the same club")

            if len(main_player_ids) > 11:
                raise FailedOperationException("Cannot add more than 11 players to the main squad")
            if len(bench_player_ids) > 4:
                raise FailedOperationException("Cannot add more than 4 players to the bench")

            await session.execute(
                delete(squad_players_association)
                .where(squad_players_association.c.squad_id == squad_id)
            )
            await session.execute(
                delete(squad_bench_players_association)
                .where(squad_bench_players_association.c.squad_id == squad_id)
            )

            for player_id in main_player_ids:
                player = player_by_id[player_id]
                squad.budget -= player.market_value
                stmt = squad_players_association.insert().values(squad_id=squad_id, player_id=player_id)
                await session.execute(stmt)

            for player_id in bench_player_ids:
                player = player_by_id[player_id]
                squad.budget -= player.market_value
                stmt = squad_bench_players_association.insert().values(squad_id=squad_id, player_id=player_id)
                await session.execute(stmt)

            squad.calculate_points()
            await session.commit()
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
