from fastapi import APIRouter, Depends, HTTPException

from app.custom_leagues.user_league.schemas import (
    UserLeagueSchema,
    UserLeagueWithStatsSchema,
    UserLeagueCreateSchema,
)
from app.custom_leagues.user_league.services import UserLeagueService
from app.users.dependencies import get_current_user
from app.users.models import User

router = APIRouter(prefix="/user_leagues", tags=["User Leagues"])

@router.post("/create", response_model=UserLeagueSchema)
async def create_user_league(
    data: UserLeagueCreateSchema,
    current_user: User = Depends(get_current_user)
):
    try:
        user_league = await UserLeagueService.create_user_league(data.model_dump(), current_user.id)
        return user_league
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/list", response_model=list[UserLeagueSchema])
async def get_user_leagues(
    current_user: User = Depends(get_current_user)
):
    try:
        user_leagues = await UserLeagueService.get_user_leagues(current_user.id)
        return user_leagues
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{user_league_id}", response_model=UserLeagueSchema)
async def get_user_league_by_id(user_league_id: int):
    try:
        user_league = await UserLeagueService.get_user_league_by_id(user_league_id)
        return user_league
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/{user_league_id}/squads/{squad_id}/join")
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

@router.delete("/{user_league_id}/squads/{squad_id}/leave")
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

@router.delete("/{user_league_id}/delete")
async def delete_user_league(
    user_league_id: int,
    current_user: User = Depends(get_current_user)
):
    try:
        await UserLeagueService.delete_user_league(user_league_id, current_user.id)
        return {"message": "User league successfully deleted"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/list/my_squad_leagues", response_model=list[UserLeagueWithStatsSchema])
async def get_my_squad_leagues(current_user: User = Depends(get_current_user)):
    try:
        leagues = await UserLeagueService.get_my_squad_leagues(current_user.id)
        return leagues
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{user_league_id}/leaderboard/{tour_id}", response_model=list[dict])
async def get_user_league_leaderboard(user_league_id: int, tour_id: int):
    leaderboard = await UserLeagueService.get_user_league_leaderboard(user_league_id, tour_id)
    if not leaderboard:
        raise HTTPException(status_code=404, detail="No data found for this user league and tour")
    return leaderboard