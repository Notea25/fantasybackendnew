from fastapi import APIRouter

from app.leagues.schemas import LeagueSchema
from app.leagues.services import LeagueService
from app.exceptions import ResourceNotFoundException

router = APIRouter(prefix="/leagues", tags=["Leagues"])


@router.get("/all")
async def list_leagues() -> list[LeagueSchema]:
    return await LeagueService.find_all()


@router.get("/id_{league_id}",)
async def get_leagues(league_id: int) -> LeagueSchema:
    res = await LeagueService.find_one_or_none(id=league_id)
    if not res:
        raise ResourceNotFoundException
    return res


@router.get("/sport_type_{sport}/")
async def get_leagues_by_sport_type(sport: int) -> list[LeagueSchema]:
    res = await LeagueService.find_filtered(sport=sport)
    if not res:
        raise ResourceNotFoundException
    return res
