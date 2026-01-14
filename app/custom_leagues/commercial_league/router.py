from fastapi import APIRouter, HTTPException
from typing import List, Optional

from app.custom_leagues.commercial_league.schemas import CommercialLeagueSchema
from app.custom_leagues.commercial_league.services import CommercialLeagueService

router = APIRouter(prefix="/commercial_leagues", tags=["Commercial Leagues"])

@router.post("/", response_model=CommercialLeagueSchema)
async def create_commercial_league(data: CommercialLeagueSchema):
    try:
        commercial_league = await CommercialLeagueService.create_commercial_league(data.model_dump())
        return commercial_league
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/", response_model=List[CommercialLeagueSchema])
async def get_commercial_leagues(league_id: Optional[int] = None):
    commercial_leagues = await CommercialLeagueService.get_commercial_leagues(league_id)
    return commercial_leagues
