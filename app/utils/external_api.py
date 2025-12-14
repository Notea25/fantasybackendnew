import logging
import httpx
from typing import Dict, List
from app.config import settings

logger = logging.getLogger(__name__)

class ExternalAPIClient:
    def __init__(self):
        self.base_url = settings.EXTERNAL_API_BASE_URL
        self.api_key = settings.EXTERNAL_API_KEY
        self.season = settings.EXTERNAL_API_SEASON

    async def fetch_league(self, league_id: int) -> Dict:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/leagues",
                params={"id": league_id, "season": self.season},
                headers={"x-apisports-key": self.api_key}
            )
            response.raise_for_status()
            data = response.json()
            logger.debug(f"API response for league {league_id}: {data}")
            if data["results"] == 0:
                logger.error(f"League {league_id} not found in API response")
                raise ValueError("League not found")
            return data["response"][0]

    async def fetch_teams(self, league_id: int) -> List[Dict]:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/teams",
                params={"league": league_id, "season": self.season},  # Уберите "page": page
                headers={"x-apisports-key": self.api_key}
            )
            response.raise_for_status()
            data = response.json()
            logger.debug(f"Full API response: {data}")
            return data.get("response", [])


    async def fetch_matches(self, league_id: int) -> List[Dict]:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/fixtures",
                params={"league": league_id, "season": self.season},
                headers={"x-apisports-key": self.api_key}
            )
            response.raise_for_status()
            data = response.json()
            logger.debug(f"Full API response for matches: {data}")
            if data.get("errors"):
                logger.error(f"API errors for matches: {data['errors']}")
                return []
            return data.get("response", [])

    async def fetch_players_in_league(self, league_id: int) -> list:
        all_players = []
        seen_player_ids = set()
        page = 1

        while True:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/players",
                    params={"league": league_id, "season": self.season, "page": page},
                    headers={"x-apisports-key": self.api_key}
                )
                response.raise_for_status()
                data = response.json()
                logger.debug(f"API response for players (page {page}): {data}")

                if data.get("errors"):
                    logger.error(f"API errors for players: {data['errors']}")
                    break

                if data["results"] == 0:
                    break

                for player in data["response"]:
                    player_id = player["player"]["id"]
                    if player_id not in seen_player_ids:
                        seen_player_ids.add(player_id)
                        all_players.append(player)

                if page >= data["paging"]["total"]:
                    break
                page += 1

        logger.debug(f"Total unique players fetched: {len(all_players)}")
        return all_players


external_api = ExternalAPIClient()
