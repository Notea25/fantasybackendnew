from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional, Dict, Any

from app.custom_leagues.club_league.schemas import ClubLeagueSchema, ClubLeagueListSchema
from app.custom_leagues.club_league.services import ClubLeagueService
from app.users.dependencies import get_current_user
from app.users.models import User
from app.utils.exceptions import ResourceNotFoundException, NotAllowedException

router = APIRouter(prefix="/club_leagues", tags=["Club Leagues"])


@router.get("/", response_model=List[ClubLeagueSchema])
async def get_club_league(league_id: int = None, team_id: int = None):
    try:
        club_leagues = await ClubLeagueService.get_club_league(league_id, team_id)
        return club_leagues
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{club_league_id}", response_model=ClubLeagueSchema)
async def get_club_league_by_id(club_league_id: int):
    try:
        club_league = await ClubLeagueService.get_club_league_by_id(club_league_id)
        return club_league
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/{club_league_id}/squads/{squad_id}")
async def add_squad_to_club_league(
    club_league_id: int,
    squad_id: int,
    current_user: User = Depends(get_current_user)
):
    try:
        club_league = await ClubLeagueService.add_squad_to_club_league(club_league_id, squad_id, current_user.id)
        return {"message": "Squad successfully added to the club league", "club_league": club_league}
    except ResourceNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except NotAllowedException as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.get("/{club_league_id}/leaderboard/{tour_id}", response_model=List[Dict[str, Any]])
async def get_club_league_leaderboard(club_league_id: int, tour_id: int):
    leaderboard = await ClubLeagueService.get_club_league_leaderboard(club_league_id, tour_id)
    if not leaderboard:
        raise HTTPException(status_code=404, detail="No data found for this club league and tour")
    return leaderboard

@router.get("/by-league/{league_id}", response_model=List[ClubLeagueListSchema])
async def get_club_leagues_by_league_id(league_id: int):
    try:
        club_leagues = await ClubLeagueService.get_club_leagues_by_league_id(league_id)
        return club_leagues
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/by-team/{team_id}/leaderboard/{tour_id}", response_model=List[Dict[str, Any]])
async def get_club_league_leaderboard_by_team(team_id: int, tour_id: int):
    leaderboard = await ClubLeagueService.get_club_league_leaderboard_by_team(team_id, tour_id)
    if not leaderboard:
        raise HTTPException(status_code=404, detail="No data found for this club league and tour")
    return leaderboard


@router.post("/add-squad-by-team/{team_id}/{squad_id}")
async def add_squad_to_club_league_by_team_id(
    team_id: int,
    squad_id: int,
    current_user: User = Depends(get_current_user)
):
    try:
        result = await ClubLeagueService.add_squad_to_club_league_by_team_id(squad_id, team_id)
        return {"message": "Squad successfully added to the club league", "result": result}
    except ResourceNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except NotAllowedException as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))