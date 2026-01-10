import logging
from typing import Optional, List, Dict, Any
from fastapi import HTTPException
from sqlalchemy.orm import joinedload, selectinload
from sqlalchemy.future import select
from sqlalchemy import delete, func, desc
from datetime import datetime
from app.matches.models import Match
from app.player_match_stats.models import PlayerMatchStats
from app.players.models import Player, player_bench_squad_tours, player_squad_tours
from app.squads.models import Squad, squad_players_association, squad_bench_players_association, SquadTour
from app.tours.models import Tour, tour_matches_association
from app.database import async_session_maker
from app.utils.base_service import BaseService
from app.utils.exceptions import ResourceNotFoundException, FailedOperationException

logger = logging.getLogger(__name__)

class SquadService(BaseService):
    model = Squad

    @classmethod
    async def create_squad(
        cls,
        name: str,
        user_id: int,
        league_id: int,
        fav_team_id: int,
        captain_id: Optional[int] = None,
        vice_captain_id: Optional[int] = None,
        main_player_ids: List[int] = [],
        bench_player_ids: List[int] = []
    ):
        logger.info(f"Creating squad {name} for user {user_id} in league {league_id}")
        async with async_session_maker() as session:
            try:
                existing_squad = await session.execute(
                    select(cls.model).where(
                        cls.model.user_id == user_id,
                        cls.model.league_id == league_id
                    )
                )
                if existing_squad.scalars().first():
                    logger.warning(f"User {user_id} already has a squad in league {league_id}")
                    raise FailedOperationException("User already has a squad in this league")

                next_tour = await cls._get_next_tour(league_id)
                logger.debug(f"Next tour for league {league_id}: {next_tour}")

                all_player_ids = main_player_ids + bench_player_ids
                players = await session.execute(
                    select(Player).where(Player.id.in_(all_player_ids))
                )
                players = players.scalars().all()
                player_by_id = {player.id: player for player in players}
                logger.debug(f"Found {len(players)} players")

                if len(players) != len(all_player_ids):
                    missing_players = set(all_player_ids) - {p.id for p in players}
                    logger.error(f"Players not found: {missing_players}")
                    raise ResourceNotFoundException("One or more players not found")

                if len(main_player_ids) != 11:
                    logger.error(f"Main squad must have exactly 11 players, got {len(main_player_ids)}")
                    raise FailedOperationException("Main squad must have exactly 11 players")
                if len(bench_player_ids) != 4:
                    logger.error(f"Bench must have exactly 4 players, got {len(bench_player_ids)}")
                    raise FailedOperationException("Bench must have exactly 4 players")

                total_cost = sum(p.market_value for p in players)
                logger.debug(f"Total players cost: {total_cost}")
                if total_cost > 100_000:
                    logger.error(f"Total players cost {total_cost} exceeds squad budget 100000")
                    raise FailedOperationException("Total players cost exceeds squad budget")

                for player in players:
                    if player.league_id != league_id:
                        logger.error(f"Player {player.id} is not from league {league_id}")
                        raise FailedOperationException("All players must be from the same league")

                club_counts = {}
                for player in players:
                    club_counts[player.team_id] = club_counts.get(player.team_id, 0) + 1
                    if club_counts[player.team_id] > 3:
                        logger.error(f"Cannot have more than 3 players from the same club {player.team_id}")
                        raise FailedOperationException("Cannot have more than 3 players from the same club")

                budget = 100_000 - total_cost
                logger.debug(f"Calculated budget: {budget}")
                if budget < 0:
                    logger.error(f"Budget cannot be negative: {budget}")
                    raise FailedOperationException("Budget cannot be negative")

                squad = cls.model(
                    name=name,
                    user_id=user_id,
                    league_id=league_id,
                    fav_team_id=fav_team_id,
                    current_tour_id=next_tour.id if next_tour else None,
                    budget=budget,
                    replacements=3,
                    captain_id=captain_id,
                    vice_captain_id=vice_captain_id,
                )
                session.add(squad)
                logger.debug(f"Created squad object: {squad}")

                await session.commit()
                await session.refresh(squad)
                logger.debug(f"Committed squad with ID: {squad.id}")

                for player_id in main_player_ids:
                    stmt = squad_players_association.insert().values(
                        squad_id=squad.id, player_id=player_id
                    )
                    await session.execute(stmt)
                    logger.debug(f"Added main player with ID: {player_id} to squad {squad.id}")

                for player_id in bench_player_ids:
                    stmt = squad_bench_players_association.insert().values(
                        squad_id=squad.id, player_id=player_id
                    )
                    await session.execute(stmt)
                    logger.debug(f"Added bench player with ID: {player_id} to squad {squad.id}")

                await session.commit()
                logger.debug(f"Committed player associations for squad {squad.id}")

                if next_tour:
                    squad_tour = SquadTour(
                        squad_id=squad.id,
                        tour_id=next_tour.id,
                        is_current=True,
                        captain_id=captain_id,
                        vice_captain_id=vice_captain_id,
                        main_players=players[:11],
                        bench_players=players[11:],
                    )
                    session.add(squad_tour)
                    await session.commit()
                    logger.debug(f"Created squad tour for squad {squad.id} and tour {next_tour.id}")

                return squad

            except Exception as e:
                await session.rollback()
                logger.error(f"Failed to create squad: {str(e)}", exc_info=True)
                raise FailedOperationException(f"Failed to create squad: {str(e)}")

    @classmethod
    async def _get_next_tour(cls, league_id: int) -> Optional[Tour]:
        now = datetime.utcnow()
        logger.debug(f"Finding next tour for league {league_id}")

        tour_start_dates = (
            select(
                tour_matches_association.c.tour_id,
                func.min(Match.date).label("start_date")
            )
            .join(Match, Match.id == tour_matches_association.c.match_id)
            .group_by(tour_matches_association.c.tour_id)
            .subquery()
        )

        stmt = (
            select(Tour)
            .join(tour_start_dates, Tour.id == tour_start_dates.c.tour_id)
            .where(
                Tour.league_id == league_id,
                tour_start_dates.c.start_date > now
            )
            .order_by(tour_start_dates.c.start_date.asc())
            .limit(1)
        )

        async with async_session_maker() as session:
            result = await session.execute(stmt)
            next_tour = result.unique().scalars().first()
            logger.debug(f"Next tour for league {league_id}: {next_tour}")
            return next_tour

    @classmethod
    async def find_one_or_none_with_relations(cls, **filter_by):
        logger.info(f"Fetching squad with relations, filter: {filter_by}")
        async with async_session_maker() as session:
            stmt = (
                select(cls.model)
                .filter_by(**filter_by)
                .options(
                    joinedload(cls.model.user),
                    joinedload(cls.model.league),
                )
            )
            result = await session.execute(stmt)
            squad = result.scalars().unique().first()
            if squad:
                logger.debug(f"Found squad {squad.id} with relations, current_tour_id: {squad.current_tour_id}")

                # Получаем основных игроков из squad_players_association
                main_players_stmt = (
                    select(Player)
                    .join(squad_players_association, Player.id == squad_players_association.c.player_id)
                    .where(squad_players_association.c.squad_id == squad.id)
                )
                main_players_result = await session.execute(main_players_stmt)
                main_players = main_players_result.scalars().all()

                # Получаем запасных игроков из squad_bench_players_association
                bench_players_stmt = (
                    select(Player)
                    .join(squad_bench_players_association, Player.id == squad_bench_players_association.c.player_id)
                    .where(squad_bench_players_association.c.squad_id == squad.id)
                )
                bench_players_result = await session.execute(bench_players_stmt)
                bench_players = bench_players_result.scalars().all()

                # Получаем очки для каждого игрока
                async def get_player_points(player_id: int) -> int:
                    stmt = (
                        select(func.sum(PlayerMatchStats.points))
                        .where(PlayerMatchStats.player_id == player_id)
                    )
                    result = await session.execute(stmt)
                    return result.scalar() or 0

                main_players_data = []
                for player in main_players:
                    points = await get_player_points(player.id)
                    main_players_data.append({
                        "id": player.id,
                        "name": player.name,
                        "team_id": player.team_id,
                        "points": points
                    })

                bench_players_data = []
                for player in bench_players:
                    points = await get_player_points(player.id)
                    bench_players_data.append({
                        "id": player.id,
                        "name": player.name,
                        "team_id": player.team_id,
                        "points": points
                    })

                squad.main_players_data = main_players_data
                squad.bench_players_data = bench_players_data
                logger.debug(
                    f"Loaded {len(main_players_data)} main players and {len(bench_players_data)} bench players")
            else:
                logger.debug(f"No squad found with filter {filter_by}")
            return squad

    @classmethod
    async def find_all_with_relations(cls):
        logger.info("Fetching all squads with relations")
        async with async_session_maker() as session:
            stmt = (
                select(cls.model)
                .options(
                    joinedload(cls.model.user),
                    joinedload(cls.model.league),
                )
            )
            result = await session.execute(stmt)
            squads = result.scalars().unique().all()
            logger.debug(f"Found {len(squads)} squads")

            for squad in squads:
                # Получаем основных игроков из squad_players_association
                main_players_stmt = (
                    select(Player)
                    .join(squad_players_association, Player.id == squad_players_association.c.player_id)
                    .where(squad_players_association.c.squad_id == squad.id)
                )
                main_players_result = await session.execute(main_players_stmt)
                main_players = main_players_result.scalars().all()

                # Получаем запасных игроков из squad_bench_players_association
                bench_players_stmt = (
                    select(Player)
                    .join(squad_bench_players_association, Player.id == squad_bench_players_association.c.player_id)
                    .where(squad_bench_players_association.c.squad_id == squad.id)
                )
                bench_players_result = await session.execute(bench_players_stmt)
                bench_players = bench_players_result.scalars().all()

                # Получаем очки для каждого игрока
                async def get_player_points(player_id: int) -> int:
                    stmt = (
                        select(func.sum(PlayerMatchStats.points))
                        .where(PlayerMatchStats.player_id == player_id)
                    )
                    result = await session.execute(stmt)
                    return result.scalar() or 0

                main_players_data = []
                for player in main_players:
                    points = await get_player_points(player.id)
                    main_players_data.append({
                        "id": player.id,
                        "name": player.name,
                        "team_id": player.team_id,
                        "points": points
                    })

                bench_players_data = []
                for player in bench_players:
                    points = await get_player_points(player.id)
                    bench_players_data.append({
                        "id": player.id,
                        "name": player.name,
                        "team_id": player.team_id,
                        "points": points
                    })

                squad.main_players_data = main_players_data
                squad.bench_players_data = bench_players_data
                logger.debug(
                    f"Loaded {len(main_players_data)} main players and {len(bench_players_data)} bench players for squad {squad.id}")

            return squads

    @classmethod
    async def find_filtered_with_relations(cls, **filter_by):
        logger.info(f"Fetching squads with relations, filter: {filter_by}")
        async with async_session_maker() as session:
            stmt = (
                select(cls.model)
                .filter_by(**filter_by)
                .options(
                    joinedload(cls.model.user),
                    joinedload(cls.model.league),
                )
            )
            result = await session.execute(stmt)
            squads = result.scalars().unique().all()
            logger.debug(f"Found {len(squads)} squads with filter {filter_by}")

            for squad in squads:
                main_players_stmt = (
                    select(Player)
                    .join(squad_players_association, Player.id == squad_players_association.c.player_id)
                    .where(squad_players_association.c.squad_id == squad.id)
                )
                main_players_result = await session.execute(main_players_stmt)
                main_players = main_players_result.scalars().all()

                # Получаем запасных игроков из squad_bench_players_association
                bench_players_stmt = (
                    select(Player)
                    .join(squad_bench_players_association, Player.id == squad_bench_players_association.c.player_id)
                    .where(squad_bench_players_association.c.squad_id == squad.id)
                )
                bench_players_result = await session.execute(bench_players_stmt)
                bench_players = bench_players_result.scalars().all()

                # Получаем очки для каждого игрока
                async def get_player_points(player_id: int) -> int:
                    stmt = (
                        select(func.sum(PlayerMatchStats.points))
                        .where(PlayerMatchStats.player_id == player_id)
                    )
                    result = await session.execute(stmt)
                    return result.scalar() or 0

                main_players_data = []
                for player in main_players:
                    points = await get_player_points(player.id)
                    main_players_data.append({
                        "id": player.id,
                        "name": player.name,
                        "team_id": player.team_id,
                        "points": points
                    })

                bench_players_data = []
                for player in bench_players:
                    points = await get_player_points(player.id)
                    bench_players_data.append({
                        "id": player.id,
                        "name": player.name,
                        "team_id": player.team_id,
                        "points": points
                    })

                squad.main_players_data = main_players_data
                squad.bench_players_data = bench_players_data
                logger.debug(
                    f"Loaded {len(main_players_data)} main players and {len(bench_players_data)} bench players for squad {squad.id}")

            return squads

    @classmethod
    async def update_squad_players(
        cls,
        squad_id: int,
        captain_id: Optional[int] = None,
        vice_captain_id: Optional[int] = None,
        main_player_ids: List[int] = [],
        bench_player_ids: List[int] = []
    ):
        logger.info(f"Updating players for squad {squad_id}")
        async with async_session_maker() as session:
            squad = await session.execute(
                select(cls.model).where(cls.model.id == squad_id)
            )
            squad = squad.scalars().first()
            if not squad:
                logger.error(f"Squad {squad_id} not found")
                raise ResourceNotFoundException("Squad not found")

            players = await session.execute(
                select(Player).where(Player.id.in_(main_player_ids + bench_player_ids))
            )
            players = players.scalars().all()
            player_by_id = {player.id: player for player in players}
            logger.debug(f"Found {len(players)} players for update")

            if len(players) != len(main_player_ids) + len(bench_player_ids):
                missing_players = set(main_player_ids + bench_player_ids) - {p.id for p in players}
                logger.error(f"Players not found: {missing_players}")
                raise ResourceNotFoundException("One or more players not found")

            club_counts = {}
            for player_id in main_player_ids + bench_player_ids:
                player = player_by_id[player_id]
                club_counts[player.team_id] = club_counts.get(player.team_id, 0) + 1
                if club_counts[player.team_id] > 3:
                    logger.error(f"Cannot have more than 3 players from the same club {player.team_id}")
                    raise FailedOperationException("Cannot have more than 3 players from the same club")

            if len(main_player_ids) > 11:
                logger.error(f"Cannot add more than 11 players to the main squad, got {len(main_player_ids)}")
                raise FailedOperationException("Cannot add more than 11 players to the main squad")
            if len(bench_player_ids) > 4:
                logger.error(f"Cannot add more than 4 players to the bench, got {len(bench_player_ids)}")
                raise FailedOperationException("Cannot add more than 4 players to the bench")

            await session.execute(
                delete(squad_players_association).where(
                    squad_players_association.c.squad_id == squad_id
                )
            )
            await session.execute(
                delete(squad_bench_players_association).where(
                    squad_bench_players_association.c.squad_id == squad_id
                )
            )

            for player_id in main_player_ids:
                stmt = squad_players_association.insert().values(
                    squad_id=squad_id, player_id=player_id
                )
                await session.execute(stmt)
                logger.debug(f"Added main player with ID: {player_id} to squad {squad_id}")

            for player_id in bench_player_ids:
                stmt = squad_bench_players_association.insert().values(
                    squad_id=squad_id, player_id=player_id
                )
                await session.execute(stmt)
                logger.debug(f"Added bench player with ID: {player_id} to squad {squad_id}")

            squad.captain_id = captain_id
            squad.vice_captain_id = vice_captain_id

            await cls._save_current_squad(squad_id)

            await session.commit()
            logger.info(f"Updated players for squad {squad_id}")
            return squad

    @classmethod
    async def _save_current_squad(cls, squad_id: int):
        logger.info(f"Saving current squad {squad_id}")
        async with async_session_maker() as session:
            squad = await session.execute(
                select(cls.model)
                .where(cls.model.id == squad_id)
            )
            squad = squad.scalars().first()

            if not squad or not squad.current_tour_id:
                logger.warning(f"No current tour for squad {squad_id}")
                return

            stmt = select(SquadTour).where(
                SquadTour.squad_id == squad_id,
                SquadTour.tour_id == squad.current_tour_id
            )
            result = await session.execute(stmt)
            squad_tour = result.scalars().first()

            if squad_tour:
                # Получаем основных игроков
                main_players_stmt = (
                    select(Player)
                    .join(player_squad_tours, Player.id == player_squad_tours.c.player_id)
                    .where(player_squad_tours.c.squad_tour_id == squad_tour.id)
                )
                main_players_result = await session.execute(main_players_stmt)
                main_players = main_players_result.scalars().all()

                # Получаем запасных игроков
                bench_players_stmt = (
                    select(Player)
                    .join(player_bench_squad_tours, Player.id == player_bench_squad_tours.c.player_id)
                    .where(player_bench_squad_tours.c.squad_tour_id == squad_tour.id)
                )
                bench_players_result = await session.execute(bench_players_stmt)
                bench_players = bench_players_result.scalars().all()

                # Получаем очки для каждого игрока
                async def get_player_points(player_id: int) -> int:
                    stmt = (
                        select(func.sum(PlayerMatchStats.points))
                        .where(PlayerMatchStats.player_id == player_id)
                    )
                    result = await session.execute(stmt)
                    return result.scalar() or 0

                main_players_data = []
                for player in main_players:
                    points = await get_player_points(player.id)
                    main_players_data.append({
                        "id": player.id,
                        "name": player.name,
                        "points": points
                    })

                bench_players_data = []
                for player in bench_players:
                    points = await get_player_points(player.id)
                    bench_players_data.append({
                        "id": player.id,
                        "name": player.name,
                        "points": points
                    })

                squad_tour.main_players_data = main_players_data
                squad_tour.bench_players_data = bench_players_data
                squad_tour.captain_id = squad.captain_id
                squad_tour.vice_captain_id = squad.vice_captain_id

                squad_tour.points = squad.calculate_points()
                await session.commit()
                logger.debug(f"Updated squad tour for squad {squad_id}")
            else:
                logger.warning(f"No squad tour found for squad {squad_id} and tour {squad.current_tour_id}")

    @classmethod
    async def rename_squad(cls, squad_id: int, user_id: int, new_name: str):
        logger.info(f"Renaming squad {squad_id} to {new_name} for user {user_id}")

        async with async_session_maker() as session:
            try:
                stmt = select(Squad).where(Squad.id == squad_id, Squad.user_id == user_id)
                result = await session.execute(stmt)
                squad = result.scalars().first()

                if not squad:
                    logger.error(f"Squad {squad_id} not found for user {user_id}")
                    raise ResourceNotFoundException("Squad not found or does not belong to user")

                squad.name = new_name
                await session.commit()
                await session.refresh(squad)

                logger.info(f"Successfully renamed squad {squad_id} to {squad.name}")
                return squad

            except Exception as e:
                await session.rollback()
                logger.error(f"Failed to rename squad {squad_id}: {str(e)}", exc_info=True)
                raise FailedOperationException(f"Failed to rename squad: {str(e)}")

    @classmethod
    async def get_leaderboard(cls, tour_id: int) -> List[Dict[str, Any]]:
        async with async_session_maker() as session:
            # Загружаем все составы (squads) для указанного тура с их владельцами
            stmt = (
                select(SquadTour)
                .where(SquadTour.tour_id == tour_id)
                .options(
                    joinedload(SquadTour.squad).joinedload(Squad.user)
                )
                .order_by(desc(SquadTour.points))
            )
            result = await session.execute(stmt)
            squad_tours = result.unique().scalars().all()

            # Получаем общее количество очков для каждого состава за все туры
            total_points_stmt = (
                select(
                    SquadTour.squad_id,
                    func.sum(SquadTour.points).label("total_points")
                )
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
    async def replace_players(
        cls,
        squad_id: int,
        captain_id: Optional[int] = None,
        vice_captain_id: Optional[int] = None,
        new_main_players: List[int] = [],
        new_bench_players: List[int] = []
    ):
        async with async_session_maker() as session:
            # Проверяем, что игроки существуют
            stmt = select(Player).where(Player.id.in_(new_main_players + new_bench_players))
            result = await session.execute(stmt)
            players = result.scalars().all()

            if len(players) != len(new_main_players) + len(new_bench_players):
                raise HTTPException(
                    status_code=404,
                    detail="One or more players not found"
                )

            # Получаем состав
            stmt = select(Squad).where(Squad.id == squad_id)
            result = await session.execute(stmt)
            squad = result.scalars().first()

            if not squad:
                raise HTTPException(
                    status_code=404,
                    detail=f"Squad with id {squad_id} not found"
                )

            # Проверяем, что капитан и вице-капитан входят в состав основных или запасных игроков
            if captain_id and captain_id not in new_main_players + new_bench_players:
                raise HTTPException(
                    status_code=400,
                    detail="Captain must be in main or bench players"
                )
            if vice_captain_id and vice_captain_id not in new_main_players + new_bench_players:
                raise HTTPException(
                    status_code=400,
                    detail="Vice-captain must be in main or bench players"
                )

            # Обновляем основных и запасных игроков
            squad.captain_id = captain_id
            squad.vice_captain_id = vice_captain_id

            # Уменьшаем количество замен
            if squad.replacements > 0:
                squad.replacements -= 1
            else:
                raise HTTPException(
                    status_code=400,
                    detail="No replacements left"
                )

            await session.commit()
            await session.refresh(squad)

            return squad

    @classmethod
    async def get_replacement_info(cls, squad_id: int) -> Dict[str, Any]:
        async with async_session_maker() as session:
            stmt = select(Squad).where(Squad.id == squad_id)
            result = await session.execute(stmt)
            squad = result.scalars().first()

            if not squad:
                raise HTTPException(
                    status_code=404,
                    detail=f"Squad with id {squad_id} not found"
                )

            return {
                "squad_id": squad.id,
                "remaining_replacements": squad.replacements,
                "max_replacements": 3
            }
