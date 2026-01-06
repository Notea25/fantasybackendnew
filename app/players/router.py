from fastapi import APIRouter
from app.utils.exceptions import ResourceNotFoundException
from app.players.schemas import PlayerSchema
from app.players.services import PlayerService

router = APIRouter(prefix="/players", tags=["Players"])

@router.get("/all")
async def list_players() -> list[PlayerSchema]:
    return await PlayerService.find_all()

@router.get("/player_{player_id}")
async def get_player(player_id: int) -> PlayerSchema:
    res = await PlayerService.find_one_or_none(id=player_id)
    if not res:
        raise ResourceNotFoundException
    return res

@router.get("/team_{team_id}")
async def get_players_by_team_id(team_id: int) -> list[PlayerSchema]:
    res = await PlayerService.find_filtered(team_id=team_id)
    if not res:
        raise ResourceNotFoundException
    return res

@router.get("/league_{league_id}")
async def get_players_by_league_id(league_id: int) -> list[PlayerSchema]:
    res = await PlayerService.find_filtered(league_id=league_id)
    if not res:
        raise ResourceNotFoundException
    return res

@router.get("/league/{league_id}/players_with_points")
async def get_players_with_total_points(league_id: int) -> list[dict]:
    return await PlayerService.find_all_with_total_points(league_id=league_id)