import datetime

from fastapi import APIRouter, Depends
from app.custom_leagues.schemas import CustomLeague, CustomLeagueCreate
from app.custom_leagues.services import CustomLeagueService
from app.users.dependencies import get_current_user
from app.utils.exceptions import CustomLeagueException, NotAllowedException, ResourceNotFoundException

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

@router.get("/commercial/registration_status")
async def get_all_commercial_leagues_registration_status():
    """
    Возвращает статус регистрации для всех коммерческих лиг
    """
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
    """
    Возвращает статус регистрации для конкретной лиги
    """
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

@classmethod
async def get_commercial_league_status(cls, league_id: int):
    """Возвращает статус коммерческой лиги с учетом текущего тура"""
    async with async_session_maker() as session:
        stmt = (
            select(CustomLeague)
            .where(CustomLeague.id == league_id)
            .options(joinedload(CustomLeague.tours))
        )
        result = await session.execute(stmt)
        league = result.scalars().first()

        if not league:
            raise ResourceNotFoundException("League not found")

        return {
            "is_open": league.is_open(),
            "has_current_tour": league.has_current_tour(),
            "is_in_timeframe": league.registration_start <= datetime.now() <= league.registration_end,
            "message": "League is open" if league.is_open() else "League is closed"
        }