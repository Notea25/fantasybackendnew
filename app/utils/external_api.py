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
        all_teams = []
        page = 1
        while True:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/teams",
                    params={"league": league_id, "season": self.season, "page": page},
                    headers={"x-apisports-key": self.api_key}
                )
                response.raise_for_status()
                data = response.json()
                if data["results"] == 0:
                    break
                all_teams.extend(data["response"])
                if page >= data["paging"]["total"]:
                    break
                page += 1
        return all_teams

    async def fetch_players(self, team_id: int) -> List[Dict]:
        all_players = []
        page = 1
        while True:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/players/squads",
                    params={"team": team_id, "page": page},
                    headers={"x-apisports-key": self.api_key}
                )
                response.raise_for_status()
                data = response.json()
                if data["results"] == 0:
                    break
                all_players.extend(data["response"][0]["players"])
                if page >= data["paging"]["total"]:
                    break
                page += 1
        return all_players

    async def fetch_matches(self, league_id: int) -> List[Dict]:
        all_matches = []
        page = 1
        while True:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/fixtures",
                    params={"league": league_id, "season": self.season, "page": page},
                    headers={"x-apisports-key": self.api_key}
                )
                response.raise_for_status()
                data = response.json()
                if data["results"] == 0:
                    break
                all_matches.extend(data["response"])
                if page >= data["paging"]["total"]:
                    break
                page += 1
        return all_matches

    async def fetch_players_in_league(self, league_id: int) -> list:
        all_players = []
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
                if data["results"] == 0:
                    break
                all_players.extend(data["response"])
                if page >= data["paging"]["total"]:
                    break
                page += 1
        return all_players

external_api = ExternalAPIClient()
