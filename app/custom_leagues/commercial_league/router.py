from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any, Optional

from app.custom_leagues.commercial_league.schemas import CommercialLeagueSchema
from app.custom_leagues.commercial_league.services import CommercialLeagueService
from app.users.dependencies import get_current_user
from app.users.models import User
from app.utils.exceptions import ResourceNotFoundException, NotAllowedException

router = APIRouter(prefix="/commercial_leagues", tags=["Commercial Leagues"])

@router.get("/", response_model=List[CommercialLeagueSchema])
async def get_commercial_leagues(league_id: int = None):
    try:
        commercial_leagues = await CommercialLeagueService.get_commercial_leagues(league_id)
        return commercial_leagues
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{commercial_league_id}", response_model=CommercialLeagueSchema)
async def get_commercial_league_by_id(commercial_league_id: int):
    try:
        commercial_league = await CommercialLeagueService.get_commercial_league_by_id(commercial_league_id)
        return commercial_league
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{commercial_league_id}/leaderboard/{tour_id}", response_model=List[Dict[str, Any]])
async def get_commercial_league_leaderboard(commercial_league_id: int, tour_id: int):
    leaderboard = await CommercialLeagueService.get_commercial_league_leaderboard(commercial_league_id, tour_id)
    if not leaderboard:
        raise HTTPException(status_code=404, detail="No data found for this commercial league and tour")
    return leaderboard


@router.post("/join/{commercial_league_id}/{squad_id}")
async def join_commercial_league(
    commercial_league_id: int,
    squad_id: int,
    current_user: User = Depends(get_current_user)
):
    try:
        result = await CommercialLeagueService.join_commercial_league(squad_id, commercial_league_id)
        return {"message": "Squad successfully joined the commercial league", "result": result}
    except ResourceNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except NotAllowedException as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
