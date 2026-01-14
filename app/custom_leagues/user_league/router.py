from fastapi import APIRouter, Depends, HTTPException
from typing import List

from app.custom_leagues.user_league.schemas import UserLeagueSchema
from app.custom_leagues.user_league.services import UserLeagueService
from app.users.dependencies import get_current_user
from app.users.models import User


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
