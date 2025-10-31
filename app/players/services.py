from sqlalchemy.future import select
from app.players.models import Player
from app.database import async_session_maker
from app.utils.external_api import external_api
from app.utils.base_service import BaseService
from app.utils.exceptions import ExternalAPIErrorException, FailedOperationException
from app.teams.services import TeamService
import httpx

class PlayerService(BaseService):
    model = Player

    @classmethod
    async def add_players_for_league(cls, league_id: int):
        try:
            teams = await TeamService.find_filtered(league_id=league_id)
        except Exception as e:
            raise FailedOperationException(msg=f"Failed to fetch teams: {e}")

        async with async_session_maker() as session:
            for team in teams:
                try:
                    players_data = await external_api.fetch_players(team.id)
                except httpx.HTTPStatusError:
                    raise ExternalAPIErrorException()
                except Exception:
                    raise ExternalAPIErrorException()

                for player_data in players_data:
                    try:
                        stmt = select(Player).where(Player.id == player_data["id"])
                        result = await session.execute(stmt)
                        existing_player = result.scalar_one_or_none()
                        if existing_player:
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
                    except Exception as e:
                        await session.rollback()
                        raise FailedOperationException(msg=f"Failed to add player: {e}")

            try:
                await session.commit()
            except Exception as e:
                await session.rollback()
                raise FailedOperationException(msg=f"Failed to commit players: {e}")
