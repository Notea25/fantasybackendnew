import logging
from sqlalchemy.future import select
from app.players.models import Player
from app.database import async_session_maker
from app.utils.external_api import external_api
from app.utils.base_service import BaseService
from app.utils.exceptions import FailedOperationException
from app.teams.services import TeamService
import httpx

logger = logging.getLogger(__name__)

class PlayerService(BaseService):
    model = Player

    @classmethod
    async def add_players_for_league(cls, league_id: int):
        try:
            teams = await TeamService.find_filtered(league_id=league_id)
            logger.info(f"Found {len(teams)} teams for league {league_id}")
        except Exception as e:
            raise FailedOperationException(msg=f"Failed to fetch teams: {e}")

        async with async_session_maker() as session:
            for team in teams:
                logger.info(f"Processing team {team.id}")
                try:
                    players_data = await external_api.fetch_players(team.id)
                    logger.info(f"Fetched {len(players_data)} players for team {team.id}")
                except httpx.HTTPStatusError as e:
                    logger.error(f"HTTP error fetching players for team {team.id}: {e}")
                    continue
                except Exception as e:
                    logger.error(f"Unexpected error fetching players for team {team.id}: {e}")
                    continue

                for player_data in players_data:
                    try:
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
                            number=player_data["number"],
                            position=player_data["position"],
                            photo=player_data["photo"],
                            team_id=team.id,
                            league_id=league_id,
                            market_value=100000,
                            sport=1
                        )
                        session.add(player)
                        logger.info(f"Added player {player_data['id']} for team {team.id}")
                    except Exception as e:
                        logger.error(f"Failed to add player {player_data.get('id', 'unknown')}: {e}")
                        await session.rollback()
                        continue

                try:
                    await session.commit()
                    logger.info(f"Committed players for team {team.id}")
                except Exception as e:
                    logger.error(f"Failed to commit players for team {team.id}: {e}")
                    await session.rollback()
                    continue
