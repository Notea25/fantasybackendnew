import logging
from datetime import datetime
from random import randint

from sqlalchemy import func, desc, case, distinct, cast, Numeric, and_, or_
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload

from app.matches.models import Match
from app.matches.schemas import MatchInTourSchema
from app.player_match_stats.models import PlayerMatchStats
from app.players.models import Player
from app.database import async_session_maker
from app.players.schemas import PlayerBaseInfoSchema, PlayerExtendedInfoSchema, PlayerFullInfoSchema, \
    PlayerWithTotalPointsSchema
from app.squads.models import Squad
from app.squad_tours.models import SquadTour, squad_tour_players, squad_tour_bench_players
from app.teams.models import Team
from app.tours.models import Tour
from app.tours.schemas import TourWithMatchesSchema
from app.utils.external_api import external_api
from app.utils.base_service import BaseService
from app.utils.exceptions import FailedOperationException, ResourceNotFoundException
import httpx

logger = logging.getLogger(__name__)

class PlayerService(BaseService):
    model = Player

    @classmethod
    async def sync_all_players(cls):
        """Синхронизирует всех игроков для всех команд из БД"""
        async with async_session_maker() as session:
            # Получаем все команды
            teams_stmt = select(Team)
            teams_result = await session.execute(teams_stmt)
            teams = teams_result.scalars().all()
            
            logger.info(f"Found {len(teams)} teams in database")
            
            total_added = 0
            total_updated = 0
            
            for team in teams:
                try:
                    # Получаем игроков для команды
                    players_data = await external_api.fetch_players_in_league(team.league_id)
                    
                    for player_response in players_data:
                        try:
                            player_data = player_response["player"]
                            statistics = player_response.get("statistics", [{}])[0]
                            team_id = statistics.get("team", {}).get("id")
                            
                            if not team_id or team_id != team.id:
                                continue
                            
                            # Проверяем существует ли игрок
                            stmt = select(Player).where(Player.id == player_data["id"])
                            result = await session.execute(stmt)
                            existing_player = result.scalar_one_or_none()
                            
                            if existing_player:
                                # Обновляем существующего игрока
                                existing_player.name = player_data["name"]
                                existing_player.age = player_data["age"]
                                existing_player.number = player_data.get("number")
                                existing_player.position = statistics.get("games", {}).get("position", "Unknown")
                                existing_player.photo = player_data.get("photo")
                                existing_player.team_id = team_id
                                total_updated += 1
                                logger.info(f"Updated player {player_data['id']}")
                            else:
                                # Добавляем нового игрока
                                player = cls.model(
                                    id=player_data["id"],
                                    name=player_data["name"],
                                    age=player_data["age"],
                                    number=player_data.get("number"),
                                    position=statistics.get("games", {}).get("position", "Unknown"),
                                    photo=player_data.get("photo"),
                                    team_id=team_id,
                                    league_id=team.league_id,
                                    market_value=randint(5000, 10000),
                                    sport=1
                                )
                                session.add(player)
                                total_added += 1
                                logger.info(f"Added player {player_data['id']}")
                        except Exception as e:
                            logger.error(f"Failed to process player {player_data.get('id', 'unknown')}: {e}")
                            continue
                    
                    await session.commit()
                except Exception as e:
                    logger.error(f"Failed to sync players for team {team.id}: {e}")
                    await session.rollback()
                    continue
            
            logger.info(f"Sync completed: {total_added} added, {total_updated} updated")
            return {"added": total_added, "updated": total_updated}

    @classmethod
    async def add_players_for_league(cls, league_id: int):
        try:
            players_data = await external_api.fetch_players_in_league(league_id)
            logger.info(f"Fetched {len(players_data)} players for league {league_id}")
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error fetching players for league {league_id}: {e}")
            raise FailedOperationException(msg=f"Failed to fetch players: {e}")
        except Exception as e:
            logger.error(f"Unexpected error fetching players for league {league_id}: {e}")
            raise FailedOperationException(msg=f"Failed to fetch players: {e}")

        async with async_session_maker() as session:
            for player_response in players_data:
                try:
                    player_data = player_response["player"]
                    statistics = player_response.get("statistics", [{}])[0]
                    team_id = statistics.get("team", {}).get("id")

                    if not team_id:
                        logger.warning(f"No team_id found for player {player_data['id']}, skipping")
                        continue

                    stmt = select(Player).where(Player.id == player_data["id"])
                    result = await session.execute(stmt)
                    existing_player = result.scalar_one_or_none()
                    if existing_player:
                        logger.warning(f"Player {player_data['id']} already exists, skipping")
                        continue

                    player = cls.model(
                        id=player_data["id"],
                        name=player_data["name"],
                        age=player_data["age"],
                        number=player_data.get("number"),
                        position=statistics.get("games", {}).get("position", "Unknown"),
                        photo=player_data.get("photo"),
                        team_id=team_id,
                        league_id=league_id,
                        market_value=randint(5000,10000),
                        sport=1
                    )
                    session.add(player)
                    logger.info(f"Added player {player_data['id']}")
                except Exception as e:
                    logger.error(f"Failed to add player {player_data.get('id', 'unknown')}: {e}")
                    await session.rollback()
                    continue
            try:
                await session.commit()
                logger.info(f"Committed players for league {league_id}")
            except Exception as e:
                logger.error(f"Failed to commit players for league {league_id}: {e}")
                await session.rollback()
                raise FailedOperationException(msg=f"Failed to commit players: {e}")

    @classmethod
    async def find_all_with_total_points(cls, league_id: int) -> list[PlayerWithTotalPointsSchema]:
        async with async_session_maker() as session:
            total_points_subq = (
                select(
                    PlayerMatchStats.player_id,
                    func.coalesce(func.sum(PlayerMatchStats.points), 0).label("total_points")
                )
                .group_by(PlayerMatchStats.player_id)
                .subquery()
            )

            stmt = (
                select(
                    Player,
                    total_points_subq.c.total_points,
                    Team.name.label("team_name"),
                    Team.logo.label("team_logo")
                )
                .join(Team, Player.team_id == Team.id)
                .outerjoin(total_points_subq, Player.id == total_points_subq.c.player_id)
                .where(Player.league_id == league_id)
            )

            result = await session.execute(stmt)
            players_with_points = result.unique().all()

            players = []
            for player, total_points, team_name, team_logo in players_with_points:
                player_schema = PlayerWithTotalPointsSchema(
                    id=player.id,
                    name=player.name,
                    team_id=player.team_id,
                    team_name=team_name,
                    team_logo=team_logo,
                    position=player.position,
                    market_value=player.market_value,
                    points=total_points
                )
                players.append(player_schema)

            return players


    @classmethod
    async def get_player_base_info(cls, player_id: int):
        async with async_session_maker() as session:
            stmt = (
                select(Player)
                .options(joinedload(Player.team))
                .where(Player.id == player_id)
            )
            result = await session.execute(stmt)
            player = result.scalar_one_or_none()

            if not player:
                raise ResourceNotFoundException

            player_base_info = PlayerBaseInfoSchema(
                id=player.id,
                name=player.name,
                photo=player.photo,
                team_id=player.team_id,
                team_name=player.team.name if player.team else "Unknown",
                team_logo=player.team.logo if player.team else None,
                position=player.position
            )

            return player_base_info

    @classmethod
    async def _get_total_players_in_league(cls, league_id: int) -> int:
        async with async_session_maker() as session:
            stmt = select(func.count()).where(Player.league_id == league_id)
            result = await session.execute(stmt)
            return result.scalar()

    @classmethod
    async def _get_market_value_rank(cls, player_id: int, league_id: int) -> int:
        async with async_session_maker() as session:
            player_market_value_stmt = select(Player.market_value).where(Player.id == player_id)
            player_market_value_result = await session.execute(player_market_value_stmt)
            player_market_value = player_market_value_result.scalar()

            rank_stmt = (
                select(func.count() + 1)
                .where(
                    Player.league_id == league_id,
                    Player.market_value > player_market_value
                )
            )
            rank_result = await session.execute(rank_stmt)
            return rank_result.scalar()

    @classmethod
    async def _get_avg_points_all_matches(cls, player_id: int, league_id: int) -> tuple[float, int]:
        async with async_session_maker() as session:
            avg_points_stmt = (
                select(func.coalesce(func.avg(PlayerMatchStats.points), 0))
                .where(PlayerMatchStats.player_id == player_id)
            )
            avg_points_result = await session.execute(avg_points_stmt)
            avg_points = avg_points_result.scalar()

            rank_stmt = (
                select(func.count() + 1)
                .select_from(Player)
                .join(PlayerMatchStats, Player.id == PlayerMatchStats.player_id, isouter=True)
                .group_by(Player.id)
                .having(func.avg(PlayerMatchStats.points) > avg_points)
                .where(Player.league_id == league_id)
            )
            rank_result = await session.execute(rank_stmt)
            rank = rank_result.scalar() or await cls._get_total_players_in_league(league_id)

            return avg_points, rank

    @classmethod
    async def _get_avg_points_last_5_matches(cls, player_id: int, league_id: int) -> tuple[float, int]:
        async with async_session_maker() as session:
            last_5_matches_stmt = (
                select(PlayerMatchStats)
                .join(Match, PlayerMatchStats.match_id == Match.id)
                .where(PlayerMatchStats.player_id == player_id)
                .order_by(desc(Match.date))
                .limit(5)
            )
            last_5_matches_result = await session.execute(last_5_matches_stmt)
            last_5_matches = last_5_matches_result.scalars().all()

            avg_points = 0
            if last_5_matches:
                avg_points = sum(match.points for match in last_5_matches) / len(last_5_matches)

            last_5_matches_subq = (
                select(PlayerMatchStats.match_id)
                .join(Match, PlayerMatchStats.match_id == Match.id)
                .where(PlayerMatchStats.player_id == Player.id)
                .order_by(desc(Match.date))
                .limit(5)
                .correlate(Player)
                .alias("last_5_matches_subq")
            )

            rank_stmt = (
                select(func.count() + 1)
                .select_from(Player)
                .join(PlayerMatchStats, Player.id == PlayerMatchStats.player_id, isouter=True)
                .join(Match, PlayerMatchStats.match_id == Match.id, isouter=True)
                .where(
                    Player.league_id == league_id,
                    PlayerMatchStats.match_id.in_(last_5_matches_subq)
                )
                .group_by(Player.id)
                .having(func.avg(PlayerMatchStats.points) > avg_points)
            )
            rank_result = await session.execute(rank_stmt)
            rank = rank_result.scalar() or await cls._get_total_players_in_league(league_id)

            return avg_points, rank

    @classmethod
    async def _get_squad_presence_percentage(cls, player_id: int, league_id: int) -> tuple[float, int]:
        async with async_session_maker() as session:
            squad_presence_stmt = (
                select(func.count())
                .select_from(SquadTour)
                .join(Squad, SquadTour.squad_id == Squad.id)
                .join(squad_tour_players, SquadTour.id == squad_tour_players.c.squad_tour_id, isouter=True)
                .where(
                    squad_tour_players.c.player_id == player_id,
                    Squad.league_id == league_id
                )
                .union_all(
                    select(func.count())
                    .select_from(SquadTour)
                    .join(Squad, SquadTour.squad_id == Squad.id)
                    .join(squad_tour_bench_players, SquadTour.id == squad_tour_bench_players.c.squad_tour_id,
                          isouter=True)
                    .where(
                        squad_tour_bench_players.c.player_id == player_id,
                        Squad.league_id == league_id
                    )
                )
                .alias("squad_presence_count")
            )

            total_squad_tours_stmt = (
                select(func.count())
                .select_from(SquadTour)
                .join(Squad, SquadTour.squad_id == Squad.id)
                .where(Squad.league_id == league_id)
            )
            total_squad_tours_result = await session.execute(total_squad_tours_stmt)
            total_squad_tours = total_squad_tours_result.scalar()

            if total_squad_tours == 0:
                total_players_in_league = await cls._get_total_players_in_league(league_id)
                return 0, total_players_in_league

            squad_presence_count_stmt = select(func.sum(squad_presence_stmt.c.count))
            squad_presence_count_result = await session.execute(squad_presence_count_stmt)
            squad_presence_count = squad_presence_count_result.scalar() or 0

            squad_presence_percentage = (squad_presence_count / total_squad_tours) * 100

            rank_stmt = (
                select(func.count() + 1)
                .select_from(Player)
                .join(Squad, Player.league_id == Squad.league_id, isouter=True)
                .join(SquadTour, Squad.id == SquadTour.squad_id, isouter=True)
                .join(squad_tour_players, SquadTour.id == squad_tour_players.c.squad_tour_id, isouter=True)
                .join(squad_tour_bench_players, SquadTour.id == squad_tour_bench_players.c.squad_tour_id, isouter=True)
                .group_by(Player.id)
                .having(
                    func.sum(
                        case(
                            (squad_tour_players.c.player_id == Player.id, 1),
                            (squad_tour_bench_players.c.player_id == Player.id, 1),
                            else_=0
                        )
                    ) / cast(func.count(distinct(SquadTour.id)), Numeric) > (squad_presence_percentage / 100)
                )
                .where(Player.league_id == league_id)
            )

            rank_result = await session.execute(rank_stmt)
            rank = rank_result.scalar()

            if rank is None:
                total_players_in_league = await cls._get_total_players_in_league(league_id)
                rank = total_players_in_league

            return squad_presence_percentage, rank

    @classmethod
    async def get_player_extended_info(cls, player_id: int, league_id: int):
        total_players_in_league = await cls._get_total_players_in_league(league_id)
        market_value_rank = await cls._get_market_value_rank(player_id, league_id)

        avg_points_all_matches, avg_points_all_matches_rank = await cls._get_avg_points_all_matches(player_id,
                                                                                                    league_id)
        avg_points_last_5_matches, avg_points_last_5_matches_rank = await cls._get_avg_points_last_5_matches(player_id,
                                                                                                             league_id)
        squad_presence_percentage, squad_presence_rank = await cls._get_squad_presence_percentage(player_id, league_id)

        player_extended_info = PlayerExtendedInfoSchema(
            total_players_in_league=total_players_in_league,
            market_value_rank=market_value_rank,
            avg_points_all_matches=avg_points_all_matches or 0,
            avg_points_all_matches_rank=avg_points_all_matches_rank,
            avg_points_last_5_matches=avg_points_last_5_matches or 0,
            avg_points_last_5_matches_rank=avg_points_last_5_matches_rank,
            squad_presence_percentage=squad_presence_percentage,
            squad_presence_rank=squad_presence_rank
        )

        return player_extended_info

    @classmethod
    async def get_last_3_tours_with_matches(cls, player_id: int) -> list[TourWithMatchesSchema]:
        async with async_session_maker() as session:
            player_stmt = select(Player).where(Player.id == player_id).options(joinedload(Player.team))
            player_result = await session.execute(player_stmt)
            player = player_result.scalar_one_or_none()

            if not player or not player.team:
                raise ResourceNotFoundException(detail=f"Player or player's team not found")

            team_id = player.team_id

            last_3_tours_stmt = (
                select(Tour)
                .join(Match, Match.tour_id == Tour.id)
                .where(
                    and_(
                        or_(
                            Match.home_team_id == team_id,
                            Match.away_team_id == team_id
                        ),
                        Match.date < datetime.utcnow()
                    )
                )
                .group_by(Tour.id)
                .order_by(desc(Tour.id))
                .limit(3)
                .options(selectinload(Tour.matches))
            )
            last_3_tours_result = await session.execute(last_3_tours_stmt)
            last_3_tours = last_3_tours_result.unique().scalars().all()

            tours_with_matches = []
            for tour in last_3_tours:
                matches_list = []
                for match in tour.matches:
                    if match.home_team_id == team_id or match.away_team_id == team_id:
                        opponent_team_id = match.away_team_id if match.home_team_id == team_id else match.home_team_id
                        opponent_team_stmt = select(Team).where(Team.id == opponent_team_id)
                        opponent_team_result = await session.execute(opponent_team_stmt)
                        opponent_team = opponent_team_result.scalar_one_or_none()

                        player_points_stmt = (
                            select(PlayerMatchStats.points)
                            .where(
                                PlayerMatchStats.player_id == player_id,
                                PlayerMatchStats.match_id == match.id
                            )
                        )
                        player_points_result = await session.execute(player_points_stmt)
                        player_points = player_points_result.scalar_one_or_none()

                        match_schema = MatchInTourSchema(
                            match_id=match.id,
                            is_home=match.home_team_id == team_id,
                            opponent_team_id=opponent_team_id,
                            opponent_team_name=opponent_team.name if opponent_team else "Unknown",
                            opponent_team_logo=opponent_team.logo if opponent_team else None,
                            player_points=player_points
                        )
                        matches_list.append(match_schema)

                tour_schema = TourWithMatchesSchema(
                    tour_id=tour.id,
                    tour_number=tour.number,
                    matches=matches_list
                )
                tours_with_matches.append(tour_schema)

            return tours_with_matches

    @classmethod
    async def get_next_3_tours_with_matches(cls, player_id: int) -> list[TourWithMatchesSchema]:
        async with async_session_maker() as session:
            player_stmt = select(Player).where(Player.id == player_id).options(joinedload(Player.team))
            player_result = await session.execute(player_stmt)
            player = player_result.scalar_one_or_none()

            if not player or not player.team:
                raise ResourceNotFoundException(detail=f"Player or player's team not found")

            team_id = player.team_id

            next_3_tours_stmt = (
                select(Tour)
                .join(Match, Match.tour_id == Tour.id)
                .where(
                    and_(
                        or_(
                            Match.home_team_id == team_id,
                            Match.away_team_id == team_id
                        ),
                        Match.date >= datetime.utcnow()
                    )
                )
                .group_by(Tour.id)
                .order_by(Tour.id)
                .limit(3)
                .options(selectinload(Tour.matches))
            )
            next_3_tours_result = await session.execute(next_3_tours_stmt)
            next_3_tours = next_3_tours_result.unique().scalars().all()

            tours_with_matches = []
            for tour in next_3_tours:
                matches_list = []
                for match in tour.matches:
                    if match.home_team_id == team_id or match.away_team_id == team_id:
                        opponent_team_id = match.away_team_id if match.home_team_id == team_id else match.home_team_id
                        opponent_team_stmt = select(Team).where(Team.id == opponent_team_id)
                        opponent_team_result = await session.execute(opponent_team_stmt)
                        opponent_team = opponent_team_result.scalar_one_or_none()

                        match_schema = MatchInTourSchema(
                            match_id=match.id,
                            is_home=match.home_team_id == team_id,
                            opponent_team_id=opponent_team_id,
                            opponent_team_name=opponent_team.name if opponent_team else "Unknown",
                            opponent_team_logo=opponent_team.logo if opponent_team else None
                        )
                        matches_list.append(match_schema)

                tour_schema = TourWithMatchesSchema(
                    tour_id=tour.id,
                    tour_number=tour.number,
                    matches=matches_list
                )
                tours_with_matches.append(tour_schema)

            return tours_with_matches


    @classmethod
    async def get_player_full_info(cls, player_id: int) -> PlayerFullInfoSchema:
        base_info = await cls.get_player_base_info(player_id)

        player_stmt = select(Player).where(Player.id == player_id).options(joinedload(Player.team))
        async with async_session_maker() as session:
            player_result = await session.execute(player_stmt)
            player = player_result.scalar_one_or_none()

            if not player or not player.team:
                raise ResourceNotFoundException(detail=f"Player or player's team not found")

            league_id = player.league_id

        extended_info = await cls.get_player_extended_info(player_id, league_id)

        last_3_tours = await cls.get_last_3_tours_with_matches(player_id)

        next_3_tours = await cls.get_next_3_tours_with_matches(player_id)

        player_full_info = PlayerFullInfoSchema(
            base_info=base_info,
            extended_info=extended_info,
            last_3_tours=last_3_tours,
            next_3_tours=next_3_tours
        )

        return player_full_info