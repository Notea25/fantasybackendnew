from fastapi import APIRouter, Depends
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
