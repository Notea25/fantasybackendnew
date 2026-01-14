from fastapi import APIRouter, HTTPException
from typing import List, Optional

from app.custom_leagues.club_league.schemas import ClubLeagueSchema
from app.custom_leagues.club_league.services import ClubLeagueService

router = APIRouter(prefix="/club_leagues", tags=["Club Leagues"])

@router.post("/", response_model=ClubLeagueSchema)
async def create_club_league(data: ClubLeagueSchema):
    try:
        club_league = await ClubLeagueService.create_club_league(data.model_dump())
        return club_league
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/", response_model=List[ClubLeagueSchema])
async def get_club_leagues(league_id: Optional[int] = None, team_id: Optional[int] = None):
    club_leagues = await ClubLeagueService.get_club_leagues(league_id, team_id)
    return club_leagues
