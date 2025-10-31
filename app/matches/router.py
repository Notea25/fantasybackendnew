from fastapi import APIRouter
from app.matches.schemas import MatchSchema
from app.matches.services import MatchService
from app.utils.exceptions import ResourceNotFoundException

router = APIRouter(prefix="/matches", tags=["Matches"])

@router.get("/all")
async def list_matches() -> list[MatchSchema]:
    return await MatchService.find_all()

@router.get("/id_{match_id}")
async def get_match(match_id: int) -> MatchSchema:
    res = await MatchService.find_one_or_none(id=match_id)
    if not res:
        raise ResourceNotFoundException
    return res

@router.get("/league_{league_id}")
async def get_matches_by_league(league_id: int) -> list[MatchSchema]:
    res = await MatchService.find_filtered(league_id=league_id)
    if not res:
        raise ResourceNotFoundException
    return res

@router.get("/team/{team_id}")
async def get_matches_by_team(team_id: int) -> list[MatchSchema]:
    res = await MatchService.find_matches_by_team(team_id=team_id)
    if not res:
        raise ResourceNotFoundException
    return res
