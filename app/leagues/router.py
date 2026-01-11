from fastapi import APIRouter, Depends

from app.leagues.schemas import LeagueSchema, LeagueMainPageSchema
from app.leagues.services import LeagueService
from app.users.dependencies import get_current_user
from app.users.models import User
from app.utils.exceptions import ResourceNotFoundException

router = APIRouter(prefix="/leagues", tags=["Leagues"])


@router.get("/all")
async def list_leagues() -> list[LeagueSchema]:
    return await LeagueService.find_all()


@router.get("/id_{league_id}",)
async def get_league(league_id: int) -> LeagueSchema:
    res = await LeagueService.find_one_or_none(id=league_id)
    if not res:
        raise ResourceNotFoundException
    return res


@router.get("/main_page_id_{league_id}", response_model=LeagueMainPageSchema)
async def get_league_main_page(
    league_id: int,
    user: User = Depends(get_current_user)
) -> LeagueMainPageSchema:
    res = await LeagueService.find_one_or_none_main_page(league_id=league_id, user_id=user.id)
    if not res:
        raise ResourceNotFoundException
    return res

# @router.get("/all_leagues_main_page", response_model=list[LeagueMainPageSchema])
# async def get_all_leagues_main_page(user: User = Depends(get_current_user)) -> list[LeagueMainPageSchema]:
#     leagues = await LeagueService.find_all_main_page(user_id=user.id)
#     return leagues
#
@router.get("/sport_type_{sport}/")
async def get_leagues_by_sport_type(sport: int) -> list[LeagueSchema]:
    res = await LeagueService.find_filtered(sport=sport)
    if not res:
        raise ResourceNotFoundException
    return res
