import logging
from typing import Optional

from fastapi import HTTPException
from sqlalchemy.orm import joinedload, selectinload
from sqlalchemy.future import select
from sqlalchemy import delete, func, desc
from datetime import datetime, timedelta

from app.matches.models import Match
from app.player_match_stats.models import PlayerMatchStats
from app.players.models import Player, player_bench_squad_tours, player_squad_tours
from app.squads.models import Squad, squad_players_association, squad_bench_players_association, SquadTour
from app.custom_leagues.user_league.models import UserLeague, user_league_squads
from app.tours.models import Tour, tour_matches_association
from app.tours.services import TourService
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
        captain_id: int,
        vice_captain_id: int,
        main_player_ids: list[int] = [],
        bench_player_ids: list[int] = []
    ):
        logger.info(f"Creating squad {name} for user {user_id} in league {league_id}")
        async with async_session_maker() as session:
            try:
                existing_squad_result = await session.execute(
                    select(cls.model).where(
                        cls.model.user_id == user_id,
                        cls.model.league_id == league_id
                    )
                )
                existing_squad = existing_squad_result.scalars().first()
                if existing_squad:
                    logger.warning(
                        f"User {user_id} already has a squad in league {league_id}, returning existing squad {existing_squad.id}"
                    )
                    return existing_squad

                # Определяем следующий тур для сквада
                previous_tour, current_tour, next_tour = await TourService.get_previous_current_next_tour(league_id)
                logger.debug(f"Tours for league {league_id}: previous={previous_tour}, current={current_tour}, next={next_tour}")
                
                # Правило: новый сквад всегда создается для следующего тура
                # (текущий тур уже идет, поэтому создавать для него нельзя)
                active_tour = next_tour
                active_tour_id = active_tour.id if active_tour else None
                logger.debug(f"Next tour for new squad: {active_tour_id}")

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

                # Бюджет больше не валидируем на этапе создания сквада,
                # но продолжаем его рассчитывать и сохранять.

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
                
                # Validate main squad positions - must match valid formation with exactly 1 GK
                main_players = [player_by_id[pid] for pid in main_player_ids]
                bench_players = [player_by_id[pid] for pid in bench_player_ids]
                
                main_position_counts = {}
                for player in main_players:
                    position = player.position
                    main_position_counts[position] = main_position_counts.get(position, 0) + 1
                
                bench_position_counts = {}
                for player in bench_players:
                    position = player.position
                    bench_position_counts[position] = bench_position_counts.get(position, 0) + 1
                
                # Must have exactly 1 GK on field and 1 on bench
                if main_position_counts.get("Goalkeeper", 0) != 1:
                    logger.error("Main squad must have exactly 1 Goalkeeper")
                    raise FailedOperationException("Main squad must have exactly 1 Goalkeeper")
                if bench_position_counts.get("Goalkeeper", 0) != 1:
                    logger.error("Bench must have exactly 1 Goalkeeper")
                    raise FailedOperationException("Bench must have exactly 1 Goalkeeper")
                
                # Check if formation is valid
                valid_formations = [
                    {"DEF": 4, "MID": 3, "FWD": 3},
                    {"DEF": 4, "MID": 4, "FWD": 2},
                    {"DEF": 3, "MID": 5, "FWD": 2},
                    {"DEF": 5, "MID": 4, "FWD": 1},
                    {"DEF": 3, "MID": 4, "FWD": 3},
                    {"DEF": 4, "MID": 5, "FWD": 1},
                    {"DEF": 5, "MID": 2, "FWD": 3},
                    {"DEF": 5, "MID": 3, "FWD": 2},
                ]
                
                defenders = main_position_counts.get("Defender", 0)
                midfielders = main_position_counts.get("Midfielder", 0)
                forwards = main_position_counts.get("Attacker", 0) + main_position_counts.get("Forward", 0)
                
                is_valid = any(
                    f["DEF"] == defenders and f["MID"] == midfielders and f["FWD"] == forwards
                    for f in valid_formations
                )
                
                if not is_valid:
                    logger.error(f"Invalid formation: {defenders}-{midfielders}-{forwards}")
                    raise FailedOperationException(f"Invalid formation ({defenders}-{midfielders}-{forwards}). Valid formations: 4-3-3, 4-4-2, 3-5-2, 5-4-1, 3-4-3, 4-5-1, 5-2-3, 5-3-2")

                budget = 100_000 - total_cost
                logger.debug(f"Calculated budget: {budget}")

                squad = cls.model(
                    name=name,
                    user_id=user_id,
                    league_id=league_id,
                    fav_team_id=fav_team_id,
                    current_tour_id=active_tour_id,
                    budget=budget,
                    replacements=2,
                    penalty_points=0,
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

                # Создаём SquadTour для следующего тура
                if active_tour_id:
                    bench_players = [player_by_id[pid] for pid in bench_player_ids]
                    
                    squad_tour = SquadTour(
                        squad_id=squad.id,
                        tour_id=active_tour_id,
                        is_current=True,
                        captain_id=captain_id,
                        vice_captain_id=vice_captain_id,
                        main_players=main_players,
                        bench_players=bench_players,
                        points=0,
                        penalty_points=0,
                    )
                    session.add(squad_tour)
                    await session.commit()
                    logger.info(f"Created SquadTour for squad {squad.id} and next tour {active_tour_id}")
                else:
                    logger.warning(f"No next tour found for league {league_id}, SquadTour not created")

                # Автоматически добавляем сквад создателя во все его пользовательские лиги
                # для этой основной лиги.
                user_leagues_stmt = select(UserLeague).where(
                    UserLeague.league_id == league_id,
                    UserLeague.creator_id == user_id,
                )
                user_leagues_result = await session.execute(user_leagues_stmt)
                user_leagues = user_leagues_result.scalars().all()

                for user_league in user_leagues:
                    link_check_stmt = select(user_league_squads).where(
                        user_league_squads.c.user_league_id == user_league.id,
                        user_league_squads.c.squad_id == squad.id,
                    )
                    link_check_result = await session.execute(link_check_stmt)
                    if not link_check_result.first():
                        insert_link_stmt = user_league_squads.insert().values(
                            user_league_id=user_league.id,
                            squad_id=squad.id,
                        )
                        await session.execute(insert_link_stmt)
                        logger.debug(
                            f"Auto-joined squad {squad.id} to user league {user_league.id} for user {user_id}"
                        )

                await session.commit()

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
    async def _get_player_total_points(cls, session, player_id: int) -> int:
        """Получить общее количество очков игрока за все матчи."""
        stmt = (
            select(func.coalesce(func.sum(PlayerMatchStats.points), 0))
            .where(PlayerMatchStats.player_id == player_id)
        )
        result = await session.execute(stmt)
        return result.scalar() or 0

    @classmethod
    async def _get_player_tour_points(cls, session, player_id: int, tour_id: int) -> int:
        """Получить очки игрока за конкретный тур."""
        from app.matches.models import Match
        from app.tours.models import tour_matches_association
        
        # Получаем матчи тура
        matches_stmt = (
            select(Match.id)
            .join(tour_matches_association, Match.id == tour_matches_association.c.match_id)
            .where(tour_matches_association.c.tour_id == tour_id)
        )
        matches_result = await session.execute(matches_stmt)
        match_ids = [row[0] for row in matches_result.all()]
        
        if not match_ids:
            return 0
        
        # Получаем очки игрока за эти матчи
        points_stmt = (
            select(func.coalesce(func.sum(PlayerMatchStats.points), 0))
            .where(
                PlayerMatchStats.player_id == player_id,
                PlayerMatchStats.match_id.in_(match_ids)
            )
        )
        result = await session.execute(points_stmt)
        return result.scalar() or 0

    @classmethod
    async def _get_current_or_last_tour_id(cls, session, league_id: int) -> Optional[int]:
        """Получить ID текущего или последнего тура.
        
        Логика:
        - Если есть текущий тур (идущий сейчас) - возвращаем его
        - Если текущего тура нет, но дедлайн следующего прошел - возвращаем следующий
        - Иначе возвращаем последний завершенный тур
        """
        previous_tour, current_tour, next_tour = await TourService.get_previous_current_next_tour(league_id)
        
        # Если идет текущий тур - возвращаем его
        if current_tour:
            return current_tour.id
        
        # Если есть следующий тур и его дедлайн прошел - возвращаем его
        if next_tour:
            from datetime import datetime, timezone
            now = datetime.utcnow().replace(tzinfo=timezone.utc)
            
            if next_tour.matches_association:
                start_date = min(association.match.date for association in next_tour.matches_association)
                deadline = start_date - timedelta(hours=2)
                
                if now >= deadline:
                    return next_tour.id
        
        # Возвращаем последний завершенный тур
        if previous_tour:
            return previous_tour.id
        
        return None

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

                main_players_stmt = (
                    select(Player)
                    .join(squad_players_association, Player.id == squad_players_association.c.player_id)
                    .where(squad_players_association.c.squad_id == squad.id)
                )
                main_players_result = await session.execute(main_players_stmt)
                main_players = main_players_result.scalars().all()

                bench_players_stmt = (
                    select(Player)
                    .join(squad_bench_players_association, Player.id == squad_bench_players_association.c.player_id)
                    .where(squad_bench_players_association.c.squad_id == squad.id)
                )
                bench_players_result = await session.execute(bench_players_stmt)
                bench_players = bench_players_result.scalars().all()

                async def get_player_points(player_id: int) -> int:
                    stmt = (
                        select(func.sum(PlayerMatchStats.points))
                        .where(PlayerMatchStats.player_id == player_id)
                    )
                    result = await session.execute(stmt)
                    return result.scalar() or 0

                main_players_stmt_full = (
                    select(Player)
                    .join(squad_players_association, Player.id == squad_players_association.c.player_id)
                    .where(squad_players_association.c.squad_id == squad.id)
                    .options(joinedload(Player.team))
                )
                main_players_result_full = await session.execute(main_players_stmt_full)
                main_players_full = main_players_result_full.unique().scalars().all()

                # Определяем текущий/последний тур
                current_or_last_tour_id = await cls._get_current_or_last_tour_id(session, squad.league_id)

                main_players_data = []
                for player in main_players_full:
                    total_points = await cls._get_player_total_points(session, player.id)
                    tour_points = 0
                    if current_or_last_tour_id:
                        tour_points = await cls._get_player_tour_points(session, player.id, current_or_last_tour_id)
                    
                    main_players_data.append({
                        "id": player.id,
                        "name": player.name,
                        "position": player.position,
                        "team_id": player.team_id,
                        "team_name": player.team.name if player.team else "",
                        "team_logo": player.team.logo if player.team else None,
                        "market_value": player.market_value,
                        "photo": player.photo,
                        "total_points": total_points,
                        "tour_points": tour_points,
                    })

                bench_players_stmt_full = (
                    select(Player)
                    .join(squad_bench_players_association, Player.id == squad_bench_players_association.c.player_id)
                    .where(squad_bench_players_association.c.squad_id == squad.id)
                    .options(joinedload(Player.team))
                )
                bench_players_result_full = await session.execute(bench_players_stmt_full)
                bench_players_full = bench_players_result_full.unique().scalars().all()

                bench_players_data = []
                for player in bench_players_full:
                    total_points = await cls._get_player_total_points(session, player.id)
                    tour_points = 0
                    if current_or_last_tour_id:
                        tour_points = await cls._get_player_tour_points(session, player.id, current_or_last_tour_id)
                    
                    bench_players_data.append({
                        "id": player.id,
                        "name": player.name,
                        "position": player.position,
                        "team_id": player.team_id,
                        "team_name": player.team.name if player.team else "",
                        "team_logo": player.team.logo if player.team else None,
                        "market_value": player.market_value,
                        "photo": player.photo,
                        "total_points": total_points,
                        "tour_points": tour_points,
                    })

                # Подготавливаем объект сквада под SquadReadSchema
                # (schema ждет поля username, main_players, bench_players)
                squad.username = squad.user.username if squad.user else ""
                squad.main_players = main_players_data
                squad.bench_players = bench_players_data

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
                main_players_stmt = (
                    select(Player)
                    .join(squad_players_association, Player.id == squad_players_association.c.player_id)
                    .where(squad_players_association.c.squad_id == squad.id)
                    .options(joinedload(Player.team))
                )
                main_players_result = await session.execute(main_players_stmt)
                main_players = main_players_result.unique().scalars().all()

                bench_players_stmt = (
                    select(Player)
                    .join(squad_bench_players_association, Player.id == squad_bench_players_association.c.player_id)
                    .where(squad_bench_players_association.c.squad_id == squad.id)
                    .options(joinedload(Player.team))
                )
                bench_players_result = await session.execute(bench_players_stmt)
                bench_players = bench_players_result.unique().scalars().all()

                # Определяем текущий/последний тур
                current_or_last_tour_id = await cls._get_current_or_last_tour_id(session, squad.league_id)

                main_players_data = []
                for player in main_players:
                    total_points = await cls._get_player_total_points(session, player.id)
                    tour_points = 0
                    if current_or_last_tour_id:
                        tour_points = await cls._get_player_tour_points(session, player.id, current_or_last_tour_id)
                    
                    main_players_data.append({
                        "id": player.id,
                        "name": player.name,
                        "position": player.position,
                        "team_id": player.team_id,
                        "team_name": player.team.name if player.team else "",
                        "team_logo": player.team.logo if player.team else None,
                        "market_value": player.market_value,
                        "photo": player.photo,
                        "total_points": total_points,
                        "tour_points": tour_points,
                    })

                bench_players_data = []
                for player in bench_players:
                    total_points = await cls._get_player_total_points(session, player.id)
                    tour_points = 0
                    if current_or_last_tour_id:
                        tour_points = await cls._get_player_tour_points(session, player.id, current_or_last_tour_id)
                    
                    bench_players_data.append({
                        "id": player.id,
                        "name": player.name,
                        "position": player.position,
                        "team_id": player.team_id,
                        "team_name": player.team.name if player.team else "",
                        "team_logo": player.team.logo if player.team else None,
                        "market_value": player.market_value,
                        "photo": player.photo,
                        "total_points": total_points,
                        "tour_points": tour_points,
                    })

                squad.username = squad.user.username if squad.user else ""
                squad.main_players = main_players_data
                squad.bench_players = bench_players_data
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
                    .options(joinedload(Player.team))
                )
                main_players_result = await session.execute(main_players_stmt)
                main_players = main_players_result.unique().scalars().all()

                bench_players_stmt = (
                    select(Player)
                    .join(squad_bench_players_association, Player.id == squad_bench_players_association.c.player_id)
                    .where(squad_bench_players_association.c.squad_id == squad.id)
                    .options(joinedload(Player.team))
                )
                bench_players_result = await session.execute(bench_players_stmt)
                bench_players = bench_players_result.unique().scalars().all()

                # Определяем текущий/последний тур
                current_or_last_tour_id = await cls._get_current_or_last_tour_id(session, squad.league_id)

                main_players_data = []
                for player in main_players:
                    total_points = await cls._get_player_total_points(session, player.id)
                    tour_points = 0
                    if current_or_last_tour_id:
                        tour_points = await cls._get_player_tour_points(session, player.id, current_or_last_tour_id)
                    
                    main_players_data.append({
                        "id": player.id,
                        "name": player.name,
                        "position": player.position,
                        "team_id": player.team_id,
                        "team_name": player.team.name if player.team else "",
                        "team_logo": player.team.logo if player.team else None,
                        "market_value": player.market_value,
                        "photo": player.photo,
                        "total_points": total_points,
                        "tour_points": tour_points,
                    })

                bench_players_data = []
                for player in bench_players:
                    total_points = await cls._get_player_total_points(session, player.id)
                    tour_points = 0
                    if current_or_last_tour_id:
                        tour_points = await cls._get_player_tour_points(session, player.id, current_or_last_tour_id)
                    
                    bench_players_data.append({
                        "id": player.id,
                        "name": player.name,
                        "position": player.position,
                        "team_id": player.team_id,
                        "team_name": player.team.name if player.team else "",
                        "team_logo": player.team.logo if player.team else None,
                        "market_value": player.market_value,
                        "photo": player.photo,
                        "total_points": total_points,
                        "tour_points": tour_points,
                    })

                squad.username = squad.user.username if squad.user else ""
                squad.main_players = main_players_data
                squad.bench_players = bench_players_data
                logger.debug(
                    f"Loaded {len(main_players_data)} main players and {len(bench_players_data)} bench players for squad {squad.id}")

            return squads

    @classmethod
    async def update_squad_players(
            cls,
            squad_id: int,
            captain_id: Optional[int] = None,
            vice_captain_id: Optional[int] = None,
            main_player_ids: list[int] = [],
            bench_player_ids: list[int] = []
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

            if captain_id and captain_id not in main_player_ids + bench_player_ids:
                raise FailedOperationException("Captain must be in main or bench players")
            if vice_captain_id and vice_captain_id not in main_player_ids + bench_player_ids:
                raise FailedOperationException("Vice-captain must be in main or bench players")

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
            
            # Validate main squad positions
            main_players = [player_by_id[pid] for pid in main_player_ids]
            main_position_counts = {}
            for player in main_players:
                position = player.position
                main_position_counts[position] = main_position_counts.get(position, 0) + 1
            
            if main_position_counts.get("Goalkeeper", 0) < 1:
                logger.error("Main squad must have at least 1 Goalkeeper")
                raise FailedOperationException("Main squad must have at least 1 Goalkeeper")
            if main_position_counts.get("Defender", 0) < 1:
                logger.error("Main squad must have at least 1 Defender")
                raise FailedOperationException("Main squad must have at least 1 Defender")
            if main_position_counts.get("Midfielder", 0) < 1:
                logger.error("Main squad must have at least 1 Midfielder")
                raise FailedOperationException("Main squad must have at least 1 Midfielder")
            if main_position_counts.get("Attacker", 0) < 1 and main_position_counts.get("Forward", 0) < 1:
                logger.error("Main squad must have at least 1 Attacker or Forward")
                raise FailedOperationException("Main squad must have at least 1 Attacker or Forward")

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
                # SquadTour существует - обновляем его
                squad_tour.points = await squad.calculate_points(session)
                squad_tour.captain_id = squad.captain_id
                squad_tour.vice_captain_id = squad.vice_captain_id
                # Синхронизируем penalty_points с Squad
                squad_tour.penalty_points = squad.penalty_points

                await session.commit()
                logger.debug(f"Updated squad tour for squad {squad_id}")
            else:
                # SquadTour не найден - создаём его на лету
                logger.info(f"Creating missing SquadTour for squad {squad_id} and tour {squad.current_tour_id}")
                
                # Получаем текущий состав из squad
                main_players_stmt = (
                    select(Player)
                    .join(squad_players_association, Player.id == squad_players_association.c.player_id)
                    .where(squad_players_association.c.squad_id == squad_id)
                )
                main_players_result = await session.execute(main_players_stmt)
                main_players = main_players_result.scalars().all()
                
                bench_players_stmt = (
                    select(Player)
                    .join(squad_bench_players_association, Player.id == squad_bench_players_association.c.player_id)
                    .where(squad_bench_players_association.c.squad_id == squad_id)
                )
                bench_players_result = await session.execute(bench_players_stmt)
                bench_players = bench_players_result.scalars().all()
                
                # Создаём новый SquadTour
                new_squad_tour = SquadTour(
                    squad_id=squad_id,
                    tour_id=squad.current_tour_id,
                    is_current=True,
                    captain_id=squad.captain_id,
                    vice_captain_id=squad.vice_captain_id,
                    main_players=main_players,
                    bench_players=bench_players,
                    points=0,
                    penalty_points=0,
                )
                session.add(new_squad_tour)
                await session.flush()  # Чтобы получить ID
                
                # Пересчитываем очки
                new_squad_tour.points = await squad.calculate_points(session)
                
                await session.commit()
                logger.info(f"Created and saved SquadTour for squad {squad_id} and tour {squad.current_tour_id}")

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
    async def get_leaderboard(cls, tour_id: int) -> list[dict]:
        async with async_session_maker() as session:
            # Проверяем, является ли этот тур текущим
            # Для текущего тура берем данные из Squad, для исторических - из SquadTour
            from app.tours.models import Tour, TourMatchAssociation
            from app.matches.models import Match
            from datetime import datetime, timezone
            
            tour_stmt = (
                select(Tour)
                .where(Tour.id == tour_id)
                .options(
                    selectinload(Tour.matches_association).joinedload(TourMatchAssociation.match)
                )
            )
            tour_result = await session.execute(tour_stmt)
            tour = tour_result.unique().scalars().first()
            
            if not tour:
                logger.warning(f"Tour {tour_id} not found")
                return []
            
            # Определяем, является ли тур текущим по датам матчей
            is_current_tour = False
            if tour.start_date and tour.end_date:
                now = datetime.utcnow().replace(tzinfo=timezone.utc)
                start_date = tour.start_date if tour.start_date.tzinfo else tour.start_date.replace(tzinfo=timezone.utc)
                end_date = tour.end_date if tour.end_date.tzinfo else tour.end_date.replace(tzinfo=timezone.utc)
                is_current_tour = start_date <= now <= end_date
            
            # Для текущего тура получаем все сквады из той же лиги
            # Для исторических туров - через JOIN с SquadTour
            if is_current_tour:
                # Для текущего тура берем все сквады по league_id
                stmt = (
                    select(Squad)
                    .where(Squad.league_id == tour.league_id)
                    .options(
                        joinedload(Squad.user)
                    )
                )
            else:
                stmt = (
                    select(Squad)
                    .join(SquadTour, Squad.id == SquadTour.squad_id)
                    .where(SquadTour.tour_id == tour_id)
                    .options(
                        joinedload(Squad.user)
                    )
                    .distinct()
                )
            
            result = await session.execute(stmt)
            squads = result.unique().scalars().all()

            # Получаем тотальные очки и штрафы из истории SquadTour
            total_points_stmt = (
                select(
                    SquadTour.squad_id,
                    func.sum(SquadTour.points).label("total_points"),
                    func.sum(SquadTour.penalty_points).label("total_penalty_points")
                )
                .group_by(SquadTour.squad_id)
            )
            total_points_result = await session.execute(total_points_stmt)
            total_points_map = {row.squad_id: row.total_points for row in total_points_result}
            total_penalty_points_map = {row.squad_id: row.total_penalty_points for row in total_points_result}

            # Формируем лидерборд
            leaderboard_with_net_points = []
            for squad in squads:
                # Для текущего тура берем tour_points и penalty_points из Squad
                if is_current_tour:
                    tour_points = squad.points
                    tour_penalty = squad.penalty_points
                else:
                    # Для исторических туров берем из SquadTour
                    squad_tour_stmt = select(SquadTour).where(
                        SquadTour.squad_id == squad.id,
                        SquadTour.tour_id == tour_id
                    )
                    squad_tour_result = await session.execute(squad_tour_stmt)
                    squad_tour = squad_tour_result.scalars().first()
                    tour_points = squad_tour.points if squad_tour else 0
                    tour_penalty = squad_tour.penalty_points if squad_tour else 0
                
                # Тотальные очки всегда из истории
                total_pts = int(total_points_map.get(squad.id, 0) or 0)
                total_pen = int(total_penalty_points_map.get(squad.id, 0) or 0)
                net_points = total_pts - total_pen
                
                leaderboard_with_net_points.append({
                    "squad": squad,
                    "tour_points": tour_points,
                    "tour_penalty": tour_penalty,
                    "total_points": total_pts,
                    "total_penalty": total_pen,
                    "net_points": net_points,
                })
            
            # Сортируем по net_points по убыванию
            leaderboard_with_net_points.sort(key=lambda x: x["net_points"], reverse=True)
            
            leaderboard: list[dict] = []
            for index, entry in enumerate(leaderboard_with_net_points, start=1):
                squad = entry["squad"]
                
                # Формат, соответствующий ожиданиям фронтенда
                leaderboard.append({
                    "place": index,
                    "squad_id": squad.id,
                    "squad_name": squad.name,
                    "user_id": squad.user.id,
                    "username": squad.user.username,
                    "tour_points": entry["tour_points"],
                    "total_points": entry["total_points"],
                    # Return tour penalty, not total penalty - frontend needs this to calculate tour_points - penalty
                    "penalty_points": entry["tour_penalty"],
                })

            return leaderboard

   

    @classmethod
    async def replace_players(
            cls,
            squad_id: int,
            captain_id: Optional[int] = None,
            vice_captain_id: Optional[int] = None,
            new_main_players: list[int] = [],
            new_bench_players: list[int] = []
    ):
        async with async_session_maker() as session:
            stmt = select(Player).where(Player.id.in_(new_main_players + new_bench_players))
            result = await session.execute(stmt)
            players = result.scalars().all()

            if len(players) != len(new_main_players) + len(new_bench_players):
                raise HTTPException(
                    status_code=404,
                    detail="One or more players not found"
                )

            stmt = select(Squad).where(Squad.id == squad_id)
            result = await session.execute(stmt)
            squad = result.scalars().first()

            if not squad:
                raise HTTPException(
                    status_code=404,
                    detail=f"Squad with id {squad_id} not found"
                )

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

            # Validate main squad positions
            player_by_id = {p.id: p for p in players}
            main_players_obj = [player_by_id[pid] for pid in new_main_players]
            main_position_counts = {}
            for player in main_players_obj:
                position = player.position
                main_position_counts[position] = main_position_counts.get(position, 0) + 1
            
            if main_position_counts.get("Goalkeeper", 0) < 1:
                raise HTTPException(
                    status_code=400,
                    detail="Main squad must have at least 1 Goalkeeper"
                )
            if main_position_counts.get("Defender", 0) < 1:
                raise HTTPException(
                    status_code=400,
                    detail="Main squad must have at least 1 Defender"
                )
            if main_position_counts.get("Midfielder", 0) < 1:
                raise HTTPException(
                    status_code=400,
                    detail="Main squad must have at least 1 Midfielder"
                )
            if main_position_counts.get("Attacker", 0) < 1 and main_position_counts.get("Forward", 0) < 1:
                raise HTTPException(
                    status_code=400,
                    detail="Main squad must have at least 1 Attacker or Forward"
                )
            
            total_cost = sum(p.market_value for p in players)
            new_budget = 100_000 - total_cost

            # При заменах больше не валидируем бюджет, разрешаем уходить в минус.

            squad.captain_id = captain_id
            squad.vice_captain_id = vice_captain_id
            squad.budget = new_budget

            # Подсчитываем количество реальных трансферов (замен)
            current_main_ids = {p.id for p in squad.current_main_players}
            current_bench_ids = {p.id for p in squad.current_bench_players}
            new_main_ids_set = set(new_main_players)
            new_bench_ids_set = set(new_bench_players)
            
            # Игроки, которых убрали из состава
            removed_players = (current_main_ids | current_bench_ids) - (new_main_ids_set | new_bench_ids_set)
            transfer_count = len(removed_players)
            
            # Логика платных/бесплатных трансферов
            free_transfers_used = 0
            paid_transfers = 0
            penalty = 0
            
            logger.info(
                f"Squad {squad_id} transfer calculation: "
                f"transfer_count={transfer_count}, "
                f"available_replacements={squad.replacements}, "
                f"current_points={squad.points}"
            )
            
            if transfer_count > 0:
                if squad.replacements >= transfer_count:
                    # Все трансферы бесплатные
                    free_transfers_used = transfer_count
                    squad.replacements -= transfer_count
                else:
                    # Часть бесплатных, часть платных
                    free_transfers_used = squad.replacements
                    paid_transfers = transfer_count - squad.replacements
                    penalty = paid_transfers * 4  # 4 очка за каждый платный трансфер
                    
                    squad.replacements = 0
                    # Накапливаем штрафы в отдельном поле
                    squad.penalty_points += penalty

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

            for player_id in new_main_players:
                stmt = squad_players_association.insert().values(
                    squad_id=squad_id, player_id=player_id
                )
                await session.execute(stmt)

            for player_id in new_bench_players:
                stmt = squad_bench_players_association.insert().values(
                    squad_id=squad_id, player_id=player_id
                )
                await session.execute(stmt)

            await session.commit()
            await session.refresh(squad)
            
            # Сохраняем snapshot текущего состава для текущего тура
            await cls._save_current_squad(squad_id)

            # Возвращаем squad и информацию о трансферах
            return {
                "squad": squad,
                "transfers_applied": transfer_count,
                "free_transfers_used": free_transfers_used,
                "paid_transfers": paid_transfers,
                "penalty": penalty,
            }

    @classmethod
    async def get_replacement_info(cls, squad_id: int) -> dict:
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
                "max_replacements": 2
            }

    @classmethod
    async def finalize_tour_for_all_squads(cls, tour_id: int, next_tour_id: int):
        """Финализировать тур и создать snapshots для следующего тура.
        
        Этот метод должен вызываться при завершении тура (после дедлайна).
        
        Для каждого сквада:
        1. Финализирует SquadTour завершенного тура (is_current = False)
        2. Создает новый SquadTour для следующего тура
        3. Обновляет Squad.current_tour_id
        
        Args:
            tour_id: ID завершенного тура
            next_tour_id: ID следующего тура
        
        Returns:
            dict с информацией о количестве обработанных сквадов
        """
        async with async_session_maker() as session:
            # Находим все сквады, у которых current_tour_id == tour_id
            stmt = (
                select(cls.model)
                .where(cls.model.current_tour_id == tour_id)
                .options(
                    joinedload(cls.model.current_main_players),
                    joinedload(cls.model.current_bench_players),
                )
            )
            result = await session.execute(stmt)
            squads = result.unique().scalars().all()
            
            finalized_count = 0
            created_count = 0
            
            for squad in squads:
                # 1. Финализируем текущий SquadTour
                current_squad_tour_stmt = (
                    select(SquadTour)
                    .where(
                        SquadTour.squad_id == squad.id,
                        SquadTour.tour_id == tour_id,
                    )
                )
                current_squad_tour_result = await session.execute(current_squad_tour_stmt)
                current_squad_tour = current_squad_tour_result.scalars().first()
                
                if current_squad_tour:
                    current_squad_tour.is_current = False
                    # Пересчитываем финальные очки
                    current_squad_tour.points = await squad.calculate_points(session)
                    finalized_count += 1
                    logger.info(f"Finalized SquadTour for squad {squad.id}, tour {tour_id}")
                
                # 2. Создаем новый SquadTour для следующего тура
                # Проверяем, не существует ли уже
                next_squad_tour_check_stmt = (
                    select(SquadTour)
                    .where(
                        SquadTour.squad_id == squad.id,
                        SquadTour.tour_id == next_tour_id,
                    )
                )
                next_squad_tour_check = await session.execute(next_squad_tour_check_stmt)
                existing_next_tour = next_squad_tour_check.scalars().first()
                
                if not existing_next_tour:
                    # Копируем текущий состав
                    new_squad_tour = SquadTour(
                        squad_id=squad.id,
                        tour_id=next_tour_id,
                        is_current=True,
                        captain_id=squad.captain_id,
                        vice_captain_id=squad.vice_captain_id,
                        main_players=list(squad.current_main_players),
                        bench_players=list(squad.current_bench_players),
                        points=0,
                        penalty_points=0,
                        used_boost=None,
                    )
                    session.add(new_squad_tour)
                    created_count += 1
                    logger.info(f"Created SquadTour for squad {squad.id}, tour {next_tour_id}")
                
                # 3. Обновляем current_tour_id
                squad.current_tour_id = next_tour_id
                
                # Сбрасываем замены на новый тур (например, +1 бесплатная замена)
                # TODO: Добавить логику пополнения замен если нужно
                # squad.replacements = min(squad.replacements + 1, 2)
            
            await session.commit()
            
            logger.info(
                f"Tour transition completed: tour {tour_id} -> {next_tour_id}. "
                f"Finalized: {finalized_count}, Created: {created_count}"
            )
            
            return {
                "finalized_tours": finalized_count,
                "created_tours": created_count,
                "total_squads_processed": len(squads),
            }

    @classmethod
    async def get_squad_tour_history_with_players(cls, squad_id: int) -> list[dict]:
        """Получить полную историю туров с составами игроков для каждого тура.
        
        Возвращает список snapshots, где каждый snapshot содержит:
        - Информацию о туре
        - Очки тура
        - Капитана и вице-капитана на тот момент
        - Список игроков основы и скамейки с их очками за этот тур
        """
        async with async_session_maker() as session:
            # Загружаем все SquadTour для данного сквада
            stmt = (
                select(SquadTour)
                .where(SquadTour.squad_id == squad_id)
                .options(
                    joinedload(SquadTour.tour),
                    joinedload(SquadTour.main_players).joinedload(Player.team),
                    joinedload(SquadTour.bench_players).joinedload(Player.team),
                )
                .order_by(SquadTour.tour_id.asc())
            )
            result = await session.execute(stmt)
            squad_tours = result.unique().scalars().all()
            
            history = []
            for squad_tour in squad_tours:
                # Получаем очки каждого игрока за данный тур
                main_players_data = []
                for player in squad_tour.main_players:
                    total_points = await cls._get_player_total_points(session, player.id)
                    tour_points = await cls._get_player_tour_points(session, player.id, squad_tour.tour_id)
                    
                    main_players_data.append({
                        "id": player.id,
                        "name": player.name,
                        "position": player.position,
                        "team_id": player.team_id,
                        "team_name": player.team.name if player.team else "",
                        "team_logo": player.team.logo if player.team else None,
                        "market_value": player.market_value,
                        "photo": player.photo,
                        "total_points": total_points,
                        "tour_points": tour_points,
                    })
                
                bench_players_data = []
                for player in squad_tour.bench_players:
                    total_points = await cls._get_player_total_points(session, player.id)
                    tour_points = await cls._get_player_tour_points(session, player.id, squad_tour.tour_id)
                    
                    bench_players_data.append({
                        "id": player.id,
                        "name": player.name,
                        "position": player.position,
                        "team_id": player.team_id,
                        "team_name": player.team.name if player.team else "",
                        "team_logo": player.team.logo if player.team else None,
                        "market_value": player.market_value,
                        "photo": player.photo,
                        "total_points": total_points,
                        "tour_points": tour_points,
                    })
                
                history.append({
                    "tour_id": squad_tour.tour_id,
                    "tour_number": squad_tour.tour.number,
                    "points": squad_tour.points,
                    "penalty_points": squad_tour.penalty_points,
                    "used_boost": squad_tour.used_boost,
                    "captain_id": squad_tour.captain_id,
                    "vice_captain_id": squad_tour.vice_captain_id,
                    "main_players": main_players_data,
                    "bench_players": bench_players_data,
                })
            
            return history

    @classmethod
    async def get_leaderboard_by_fav_team(cls, tour_id: int, fav_team_id: int) -> list[dict]:
        """Лидерборд по клубной лиге (по fav_team_id).

        Формат соответствует типу CustomLeagueLeaderboardEntry на фронтенде:
        place, squad_id, squad_name, user_id, username, tour_points, total_points,
        fav_team_id, fav_team_name.
        """
        async with async_session_maker() as session:
            # Проверяем, является ли этот тур текущим
            from app.tours.models import Tour, TourMatchAssociation
            from app.matches.models import Match
            from datetime import datetime, timezone
            
            tour_stmt = (
                select(Tour)
                .where(Tour.id == tour_id)
                .options(
                    selectinload(Tour.matches_association).joinedload(TourMatchAssociation.match)
                )
            )
            tour_result = await session.execute(tour_stmt)
            tour = tour_result.unique().scalars().first()
            
            if not tour:
                logger.warning(f"Tour {tour_id} not found")
                return []
            
            # Определяем, является ли тур текущим по датам матчей
            is_current_tour = False
            if tour.start_date and tour.end_date:
                now = datetime.utcnow().replace(tzinfo=timezone.utc)
                start_date = tour.start_date if tour.start_date.tzinfo else tour.start_date.replace(tzinfo=timezone.utc)
                end_date = tour.end_date if tour.end_date.tzinfo else tour.end_date.replace(tzinfo=timezone.utc)
                is_current_tour = start_date <= now <= end_date
            
            # Для текущего тура - сквады по league_id и fav_team_id
            # Для исторических - через JOIN с SquadTour
            if is_current_tour:
                stmt = (
                    select(Squad)
                    .where(
                        Squad.league_id == tour.league_id,
                        Squad.fav_team_id == fav_team_id,
                    )
                    .options(
                        joinedload(Squad.user),
                        joinedload(Squad.fav_team),
                    )
                )
            else:
                stmt = (
                    select(Squad)
                    .join(SquadTour, Squad.id == SquadTour.squad_id)
                    .where(
                        SquadTour.tour_id == tour_id,
                        Squad.fav_team_id == fav_team_id,
                    )
                    .options(
                        joinedload(Squad.user),
                        joinedload(Squad.fav_team),
                    )
                    .distinct()
                )
            
            result = await session.execute(stmt)
            squads = result.unique().scalars().all()

            # Получаем тотальные очки и штрафы
            total_points_stmt = (
                select(
                    SquadTour.squad_id,
                    func.sum(SquadTour.points).label("total_points"),
                    func.sum(SquadTour.penalty_points).label("total_penalty_points")
                )
                .join(SquadTour.squad)
                .where(Squad.fav_team_id == fav_team_id)
                .group_by(SquadTour.squad_id)
            )
            total_points_result = await session.execute(total_points_stmt)
            total_points_map = {row.squad_id: row.total_points for row in total_points_result}
            total_penalty_points_map = {row.squad_id: row.total_penalty_points for row in total_points_result}

            # Формируем лидерборд
            leaderboard_with_net_points = []
            for squad in squads:
                # Для текущего тура берем данные из Squad
                if is_current_tour:
                    tour_points = squad.points
                    tour_penalty = squad.penalty_points
                else:
                    # Для исторических туров берем из SquadTour
                    squad_tour_stmt = select(SquadTour).where(
                        SquadTour.squad_id == squad.id,
                        SquadTour.tour_id == tour_id
                    )
                    squad_tour_result = await session.execute(squad_tour_stmt)
                    squad_tour = squad_tour_result.scalars().first()
                    tour_points = squad_tour.points if squad_tour else 0
                    tour_penalty = squad_tour.penalty_points if squad_tour else 0
                
                fav_team = getattr(squad, "fav_team", None)
                total_pts = int(total_points_map.get(squad.id, 0) or 0)
                total_pen = int(total_penalty_points_map.get(squad.id, 0) or 0)
                net_points = total_pts - total_pen
                
                leaderboard_with_net_points.append({
                    "squad": squad,
                    "fav_team": fav_team,
                    "tour_points": tour_points,
                    "tour_penalty": tour_penalty,
                    "total_points": total_pts,
                    "total_penalty": total_pen,
                    "net_points": net_points,
                })
            
            # Сортируем по net_points по убыванию
            leaderboard_with_net_points.sort(key=lambda x: x["net_points"], reverse=True)
            
            leaderboard: list[dict] = []
            for index, entry in enumerate(leaderboard_with_net_points, start=1):
                squad = entry["squad"]
                fav_team = entry["fav_team"]
                
                leaderboard.append({
                    "place": index,
                    "squad_id": squad.id,
                    "squad_name": squad.name,
                    "user_id": squad.user.id,
                    "username": squad.user.username,
                    "tour_points": entry["tour_points"],
                    "total_points": entry["total_points"],
                    # Return tour penalty, not total penalty - frontend needs this to calculate tour_points - penalty
                    "penalty_points": entry["tour_penalty"],
                    "fav_team_id": squad.fav_team_id,
                    "fav_team_name": fav_team.name if fav_team is not None else None,
                })

            return leaderboard
