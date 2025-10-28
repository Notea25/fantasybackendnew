import httpx
from fastapi import APIRouter, HTTPException, status

from app.leagues.services import LeagueService
from app.utils.external_api import external_api
from app.config import settings

router = APIRouter(prefix="/utils", tags=["Utils"])

@router.post("/{league_id}/add")
async def add_league(league_id: int):
    try:
        league = await LeagueService.add_league(league_id)
        return {"status": "success", "league_id": league.id, "league_name": league.name}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add league: {e}"
        )