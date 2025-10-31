import logging

import httpx
from typing import Dict, List
from app.config import settings


logger = logging.getLogger(__name__)

class ExternalAPIClient:
    def __init__(self):
        self.base_url = settings.EXTERNAL_API_BASE_URL
        self.api_key = settings.EXTERNAL_API_KEY

    async def fetch_league(self, league_id: int) -> Dict:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/leagues",
                params={"id": league_id, "season": settings.EXTERNAL_API_SEASON},
                headers={"x-apisports-key": self.api_key}
            )
            response.raise_for_status()
            data = response.json()
            if data["results"] == 0:
                raise ValueError("League not found")
            return data["response"][0]["league"]

    async def fetch_teams(self, league_id: int) -> List[Dict]:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/teams",
                params={"league": league_id, "season": settings.EXTERNAL_API_SEASON},
                headers={"x-apisports-key": self.api_key}
            )
            response.raise_for_status()
            data = response.json()
            if data["results"] == 0:
                raise ValueError("No teams found")
            return data["response"]

    async def fetch_players(self, team_id: int) -> List[Dict]:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/players/squads",
                params={"team": team_id},
                headers={"x-apisports-key": self.api_key}
            )
            response.raise_for_status()
            data = response.json()
            if data["results"] == 0:
                raise ValueError("No players found")
            return data["response"][0]["players"]

    async def fetch_matches(self, league_id: int) -> List[Dict]:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/fixtures",
                params={"league": league_id, "season": settings.EXTERNAL_API_SEASON},
                headers={"x-apisports-key": self.api_key}
            )
            response.raise_for_status()
            data = response.json()
            if data["results"] == 0:
                raise ValueError("No matches found")
            return data["response"]

    async def fetch_players_in_league(self, league_id: int) -> list:
        all_players = []
        page = 1
        season = settings.EXTERNAL_API_SEASON

        while True:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/players",
                    params={"league": league_id, "season": season, "page": page},
                    headers={"x-apisports-key": self.api_key}
                )
                response.raise_for_status()
                data = response.json()

                if data["results"] == 0:
                    break

                all_players.extend(data["response"])
                page += 1

                if page > data["paging"]["total"]:
                    break

        return all_players

external_api = ExternalAPIClient()
