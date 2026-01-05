from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from app.tours.schemas import TourRead
from app.tours.services import TourService
from app.users.dependencies import get_current_user
from app.users.models import User
from app.utils.exceptions import ResourceNotFoundException

router = APIRouter(prefix="/tours", tags=["Tours"])

@router.get("/get_tour_{tour_id}", response_model=TourRead)
async def get_tour(tour_id: int, user: User = Depends(get_current_user)) -> TourRead:
    tour = await TourService.find_one_or_none_with_relations(tour_id=tour_id)
    if not tour:
        raise ResourceNotFoundException()
    return tour

@router.get("/list_tours", response_model=list[TourRead])
async def list_tours(user: User = Depends(get_current_user)) -> list[TourRead]:
    tours = await TourService.find_all_with_relations()
    return tours

@router.get("/get_tour_by_number/{league_id}/{number}", response_model=TourRead)
async def get_tour_by_number(league_id: int, number: int, user: User = Depends(get_current_user)) -> TourRead:
    tour = await TourService.find_one_by_number(number=number, league_id=league_id)
    if not tour:
        raise ResourceNotFoundException()
    return tour

@router.get(
    "/get_tours_by_league/{league_id}",
    response_model=list[TourRead]
)
async def get_tours_by_league(
    league_id: int,
    user: User = Depends(get_current_user)
) -> list[TourRead]:
    tours = await TourService.find_all_by_league(league_id=league_id)
    return tours

@router.get("/get_deadline_for_next_tour/{league_id}")
async def get_deadline_for_next_tour(league_id: int):
    try:
        deadline = await TourService.get_deadline_for_next_tour(league_id=league_id)
        return {"deadline": deadline.isoformat()}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while fetching the deadline: {str(e)}"
        )

