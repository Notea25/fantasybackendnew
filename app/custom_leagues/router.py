from fastapi import APIRouter, Depends
from app.custom_leagues.schemas import CustomLeague, CustomLeagueCreate
from app.custom_leagues.services import CustomLeagueService
from app.users.dependencies import get_current_user
from app.utils.exceptions import CustomLeagueException, NotAllowedException

router = APIRouter(prefix="/custom_leagues", tags=["Custom Leagues"])

@router.post("/")
async def create_custom_league(
    data: CustomLeagueCreate,
    current_user: dict = Depends(get_current_user)
):
    try:
        return await CustomLeagueService.create_custom_league(data.model_dump(), current_user['id'])
    except CustomLeagueException as e:
        raise e
    except NotAllowedException as e:
        raise e

@router.delete("/{custom_league_id}")
async def delete_custom_league(
    custom_league_id: int,
    current_user: dict = Depends(get_current_user)
):
    try:
        return await CustomLeagueService.delete_custom_league(custom_league_id, current_user['id'])
    except NotAllowedException as e:
        raise e
