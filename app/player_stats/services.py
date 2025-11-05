from sqlalchemy.future import select
from sqlalchemy import update as sql_update
from app.player_stats.models import PlayerStats
from app.player_stats.schemas import PlayerStatsCreateSchema
from app.players.models import Player
from app.teams.models import Team
from app.database import async_session_maker
from app.utils.count_points import calculate_points
from app.utils.external_api import external_api
from app.config import settings
from app.utils.base_service import BaseService
from app.utils.exceptions import ExternalAPIErrorException, FailedOperationException
import httpx
import logging

logger = logging.getLogger(__name__)

class PlayerStatsService(BaseService):
    model = PlayerStats

    @classmethod
    async def add_player_stats_for_league(cls, league_id: int):
        try:
            players = await cls._fetch_players_in_league(league_id)
        except Exception as e:
            logger.error(f"Failed to fetch players for league {league_id}: {e}")
            raise FailedOperationException(msg=f"Failed to fetch players: {e}")

        async with async_session_maker() as session:
            for player_response in players:
                try:
                    player_data = player_response["player"]
                    statistics = player_response["statistics"][0]

                    player_id = player_data["id"]
                    team_id = statistics["team"]["id"]

                    player_stmt = select(Player).where(Player.id == player_id)
                    player_result = await session.execute(player_stmt)
                    player_exists = player_result.scalar_one_or_none()
                    if not player_exists:
                        logger.warning(f"Player {player_id} not found in database, skipping...")
                        continue

                    team_stmt = select(Team).where(Team.id == team_id)
                    team_result = await session.execute(team_stmt)
                    team_exists = team_result.scalar_one_or_none()
                    if not team_exists:
                        logger.warning(f"Team {team_id} not found in database, skipping...")
                        continue

                    player_stats_data = {
                        "player_id": player_id,
                        "league_id": league_id,
                        "team_id": team_id,
                        "season": settings.EXTERNAL_API_SEASON,
                        "appearances": statistics["games"].get("appearances"),
                        "lineups": statistics["games"].get("lineups"),
                        "minutes_played": statistics["games"].get("minutes"),
                        "position": statistics["games"].get("position"),
                        "goals_total": statistics["goals"].get("total"),
                        "assists": statistics["goals"].get("assists"),
                        "yellow_cards": statistics["cards"].get("yellow"),
                        "yellow_red_cards": statistics["cards"].get("yellowred"),
                        "red_cards": statistics["cards"].get("red"),
                        "penalty_scored": statistics["penalty"].get("scored"),
                        "penalty_missed": statistics["penalty"].get("missed"),
                        "penalty_saved": statistics["penalty"].get("saved"),
                        "points": calculate_points(statistics)
                    }

                    stats_schema = PlayerStatsCreateSchema(**player_stats_data)
                    stats_dict = stats_schema.model_dump(exclude_none=True)

                    stmt = select(PlayerStats).where(
                        PlayerStats.player_id == player_id,
                        PlayerStats.league_id == league_id,
                        PlayerStats.season == settings.EXTERNAL_API_SEASON
                    )
                    result = await session.execute(stmt)
                    existing_stats = result.scalar_one_or_none()

                    if existing_stats:
                        update_stmt = (
                            sql_update(PlayerStats)
                            .where(PlayerStats.id == existing_stats.id)
                            .values(**stats_dict)
                        )
                        await session.execute(update_stmt)
                        logger.info(f"Updated stats for player {player_id} in league {league_id}")
                    else:
                        player_stats = cls.model(**stats_dict)
                        session.add(player_stats)
                        logger.info(f"Added stats for player {player_id} in league {league_id}")
                except Exception as e:
                    logger.error(f"Error processing stats for player {player_id}: {e}")
                    await session.rollback()
                    continue
            try:
                await session.commit()
                logger.info(f"Successfully committed player stats for league {league_id}")
            except Exception as e:
                logger.error(f"Failed to commit player stats: {e}")
                await session.rollback()
                raise FailedOperationException(msg=f"Failed to commit player stats: {e}")

    @classmethod
    async def _fetch_players_in_league(cls, league_id: int) -> list:
        try:
            response = await external_api.fetch_players_in_league(league_id)
            return response
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error fetching players for league {league_id}: {e}")
            raise ExternalAPIErrorException()
        except Exception as e:
            logger.error(f"Unexpected error fetching players for league {league_id}: {e}")
            raise ExternalAPIErrorException()
