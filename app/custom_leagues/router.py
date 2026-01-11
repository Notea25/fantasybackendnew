import datetime

from fastapi import APIRouter, Depends, HTTPException
from app.custom_leagues.schemas import CustomLeague, CustomLeagueCreate, CustomLeagueSchema
from app.custom_leagues.services import CustomLeagueService
from app.users.dependencies import get_current_user
from app.users.models import User
from app.utils.exceptions import CustomLeagueException, NotAllowedException, ResourceNotFoundException

router = APIRouter(prefix="/custom_leagues", tags=["Custom Leagues"])

@router.post("/")
async def create_custom_league(
    data: CustomLeagueCreate,
    current_user: User = Depends(get_current_user)
):
    try:
        return await CustomLeagueService.create_custom_league(data.model_dump(), current_user.id)
    except CustomLeagueException as e:
        raise HTTPException(status_code=403, detail=str(e))
    except NotAllowedException as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ResourceNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.delete("/{custom_league_id}")
async def delete_custom_league(
    custom_league_id: int,
    current_user: dict = Depends(get_current_user)
):
    try:
        return await CustomLeagueService.delete_custom_league(custom_league_id, current_user['id'])
    except NotAllowedException as e:
        raise e

@router.get("/commercial/registration_status")
async def get_all_commercial_leagues_registration_status():
    commercial_leagues = await CustomLeagueService.get_all_commercial_leagues()

    result = []
    for league in commercial_leagues:
        now = datetime.now()
        is_open = league.registration_start <= now <= league.registration_end if league.registration_start and league.registration_end else False

        result.append({
            "id": league.id,
            "name": league.name,
            "is_open": is_open,
            "registration_start": league.registration_start,
            "registration_end": league.registration_end,
            "message": "Registration is open" if is_open else "Registration is closed"
        })

    return {"commercial_leagues": result}

@router.get("/{custom_league_id}/registration_status")
async def get_registration_status(custom_league_id: int):
    custom_league = await CustomLeagueService.get_by_id(custom_league_id)
    if not custom_league:
        raise ResourceNotFoundException("Custom league not found")

    now = datetime.now()
    is_open = custom_league.registration_start <= now <= custom_league.registration_end if custom_league.registration_start and custom_league.registration_end else False

    return {
        "is_open": is_open,
        "registration_start": custom_league.registration_start,
        "registration_end": custom_league.registration_end,
        "message": "Registration is open" if is_open else "Registration is closed"
    }

@router.get("/club/{custom_league_id}")
async def get_club_league(custom_league_id: int):
    custom_league = await CustomLeagueService.get_club_league(custom_league_id)
    if not custom_league:
        raise ResourceNotFoundException("Custom league not found")

    return {
        "id": custom_league.id,
        "name": custom_league.name,
        "team_name": custom_league.team.name if custom_league.team else None,
        "type": custom_league.type,
        "registration_start": custom_league.registration_start,
        "registration_end": custom_league.registration_end,
    }


@router.get("/all", response_model=list[CustomLeagueSchema])
async def get_all_custom_leagues():
    leagues = await CustomLeagueService.get_all_custom_leagues()
    return leagues

@router.get("/by_league/{league_id}", response_model=list[CustomLeagueSchema])
async def get_custom_leagues_by_league(league_id: int):
    leagues = await CustomLeagueService.get_custom_leagues_by_league_id(league_id)
    return leagues

@router.get("/by_type/{league_type}", response_model=list[CustomLeagueSchema])
async def get_custom_leagues_by_type(league_type: str):
    leagues = await CustomLeagueService.get_custom_leagues_by_type(league_type)
    return leagues

@router.post("/{custom_league_id}/squads/{squad_id}")
async def add_squad_to_custom_league(
    custom_league_id: int,
    squad_id: int,
    current_user: User = Depends(get_current_user)
):
    try:
        custom_league = await CustomLeagueService.add_squad_to_custom_league(custom_league_id, squad_id, current_user.id)
        return {"message": "Squad successfully added to the custom league", "custom_league": custom_league}
    except ResourceNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except NotAllowedException as e:
        raise HTTPException(status_code=403, detail=str(e))

@router.get("/club/by_team/{team_id}", response_model=list[CustomLeagueSchema])
async def get_club_custom_league_by_team(team_id: int):
    leagues = await CustomLeagueService.get_club_custom_league_by_team_id(team_id)
    if not leagues:
        raise HTTPException(status_code=404, detail="No club custom leagues found for this team_id")
    return leagues