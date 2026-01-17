from fastapi import APIRouter, Depends, HTTPException
from typing import List

from app.custom_leagues.user_league.schemas import UserLeagueSchema
from app.custom_leagues.user_league.services import UserLeagueService
from app.users.dependencies import get_current_user
from app.users.models import User
from app.utils.exceptions import ResourceNotFoundException, NotAllowedException

router = APIRouter(prefix="/user_leagues", tags=["User Leagues"])

@router.post("/", response_model=UserLeagueSchema)
async def create_user_league(
    data: UserLeagueSchema,
    current_user: User = Depends(get_current_user)
):
    try:
        user_league = await UserLeagueService.create_user_league(data.model_dump(), current_user.id)
        return user_league
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/", response_model=List[UserLeagueSchema])
async def get_user_leagues(
    current_user: User = Depends(get_current_user)
):
    user_leagues = await UserLeagueService.get_user_leagues(current_user.id)
    return user_leagues

@router.get("/{user_league_id}", response_model=UserLeagueSchema)
async def get_user_league_by_id(user_league_id: int):
    try:
        user_league = await UserLeagueService.get_user_league_by_id(user_league_id)
        return user_league
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/{user_league_id}/squads/{squad_id}")
async def add_squad_to_user_league(
    user_league_id: int,
    squad_id: int,
    current_user: User = Depends(get_current_user)
):
    try:
        user_league = await UserLeagueService.add_squad_to_user_league(user_league_id, squad_id, current_user.id)
        return {"message": "Squad successfully added to the user league", "user_league": user_league}
    except ResourceNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except NotAllowedException as e:
        raise HTTPException(status_code=403, detail=str(e))
