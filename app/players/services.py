import logging
from random import randint

from sqlalchemy import func
from sqlalchemy.future import select

from app.player_match_stats.models import PlayerMatchStats
from app.players.models import Player
from app.database import async_session_maker
from app.utils.external_api import external_api
from app.utils.base_service import BaseService
from app.utils.exceptions import FailedOperationException
import httpx

logger = logging.getLogger(__name__)

class PlayerService(BaseService):
    model = Player

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
    async def find_all_with_total_points(cls, league_id: int):
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
                    total_points_subq.c.total_points
                )
                .outerjoin(
                    total_points_subq,
                    Player.id == total_points_subq.c.player_id
                )
                .where(Player.league_id == league_id)
            )

            result = await session.execute(stmt)
            players_with_points = result.unique().all()

            players = []
            for player, total_points in players_with_points:
                player_dict = {
                    "id": player.id,
                    "name": player.name,
                    "team_id": player.team_id,
                    "position": player.position,
                    "market_value": player.market_value,
                    "points": total_points if total_points is not None else 0,
                }
                players.append(player_dict)

            return players
