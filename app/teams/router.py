from fastapi import APIRouter

from app.teams.schemas import TeamRead
from app.teams.services import TeamService
from app.exceptions import ResourceNotFoundException

router = APIRouter(prefix="/teams", tags=["Teams"])


@router.get("/all")
async def list_teams() -> list[TeamRead]:
    return await TeamService.find_all()


@router.get("/id_{team_id}")
async def get_teams(team_id: int) -> TeamRead:
    res = await TeamService.find_one_or_none(id=team_id)
    if not res:
        raise ResourceNotFoundException
    return res


@router.get("/league_{league_id}")
async def get_teams_by_league(league_id: int) -> list[TeamRead]:
    res = await TeamService.find_filtered(league_id=league_id)
    if not res:
        raise ResourceNotFoundException
    return res
