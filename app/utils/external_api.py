import httpx
from typing import Dict, List
from app.config import settings

class ExternalAPIClient:
    def __init__(self):
        self.base_url = settings.EXTERNAL_API_BASE_URL
        self.api_key = settings.EXTERNAL_API_KEY

    async def fetch_league(self, league_id: int, season: str) -> Dict:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/leagues",
                params={"id": league_id, "season": season},
                headers={"x-apisports-key": self.api_key}
            )
            response.raise_for_status()
            data = response.json()
            if data["results"] == 0:
                raise ValueError("League not found")
            return data["response"][0]["league"]

    async def fetch_teams(self, league_id: int, season: str) -> List[Dict]:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/teams",
                params={"league": league_id, "season": season},
                headers={"x-apisports-key": self.api_key}
            )
            response.raise_for_status()
            data = response.json()
            if data["results"] == 0:
                raise ValueError("No teams found")
            return data["response"]

    async def fetch_players(self, team_id: int, season: str) -> List[Dict]:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/players",
                params={"team": team_id, "season": season},
                headers={"x-apisports-key": self.api_key}
            )
            response.raise_for_status()
            data = response.json()
            if data["results"] == 0:
                raise ValueError("No players found")
            return data["response"]

    async def fetch_matches(self, league_id: int, season: str) -> List[Dict]:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/fixtures",
                params={"league": league_id, "season": season},
                headers={"x-apisports-key": self.api_key}
            )
            response.raise_for_status()
            data = response.json()
            if data["results"] == 0:
                raise ValueError("No matches found")
            return data["response"]

    async def fetch_player_match_stats(self, match_id: int) -> List[Dict]:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/fixtures/players",
                params={"fixture": match_id},
                headers={"x-apisports-key": self.api_key}
            )
            response.raise_for_status()
            data = response.json()
            if data["results"] == 0:
                raise ValueError("No player match stats found")
            return data["response"]

external_api = ExternalAPIClient()
