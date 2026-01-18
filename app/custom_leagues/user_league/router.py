from fastapi import APIRouter, Depends, HTTPException
from typing import List

from app.custom_leagues.user_league.schemas import UserLeagueSchema, UserLeagueWithStatsSchema, UserLeagueCreateSchema
from app.custom_leagues.user_league.services import UserLeagueService
from app.users.dependencies import get_current_user
from app.users.models import User


router = APIRouter(prefix="/user_leagues", tags=["User Leagues"])

@router.post("/", response_model=UserLeagueSchema)
async def create_user_league(
    data: UserLeagueCreateSchema,
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
async def join_user_league(
    user_league_id: int,
    squad_id: int,
    current_user: User = Depends(get_current_user)
):
    try:
        user_league = await UserLeagueService.join_user_league(user_league_id, squad_id, current_user.id)
        return {"message": "Squad successfully joined the user league", "user_league": user_league}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{user_league_id}/squads/{squad_id}")
async def leave_user_league(
    user_league_id: int,
    squad_id: int,
    current_user: User = Depends(get_current_user)
):
    try:
        user_league = await UserLeagueService.leave_user_league(user_league_id, squad_id, current_user.id)
        return {"message": "Squad successfully left the user league", "user_league": user_league}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{user_league_id}")
async def delete_user_league(
    user_league_id: int,
    current_user: User = Depends(get_current_user)
):
    try:
        await UserLeagueService.delete_user_league(user_league_id, current_user.id)
        return {"message": "User league successfully deleted"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/my-squad-leagues", response_model=List[UserLeagueWithStatsSchema])
async def get_my_squad_leagues(current_user: User = Depends(get_current_user)):
    leagues = await UserLeagueService.get_my_squad_leagues(current_user.id)
    return leagues
