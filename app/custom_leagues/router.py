from fastapi import APIRouter
from app.custom_leagues.schemas import CustomLeague, CustomLeagueCreate
from app.custom_leagues.services import CustomLeagueService

router = APIRouter(prefix="/custom_leagues", tags=["Custom Leagues"])

@router.post("/")
async def create_custom_league(data: CustomLeagueCreate):
    return await CustomLeagueService.create_custom_league(data.model_dump())

@router.get("/{custom_league_id}")
async def get_custom_league(custom_league_id: int):
    return await CustomLeagueService.get_by_id(custom_league_id)

@router.post("/{custom_league_id}/tours/{tour_id}")
async def add_tour_to_custom_league(custom_league_id: int, tour_id: int):
    return await CustomLeagueService.add_tour(custom_league_id, tour_id)

@router.post("/{custom_league_id}/squads/{squad_id}")
async def add_squad_to_custom_league(custom_league_id: int, squad_id: int):
    return await CustomLeagueService.add_squad(custom_league_id, squad_id)
