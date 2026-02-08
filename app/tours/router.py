from typing import Optional

from fastapi import APIRouter, Depends, HTTPException

from app.tours.models import Tour
from app.tours.schemas import TourRead, TourReadWithType
from app.tours.services import TourService
from app.users.dependencies import get_current_user
from app.users.models import User
from app.utils.exceptions import ResourceNotFoundException
from app.squads.services import SquadService

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

def tour_to_dict(tour: Tour) -> dict:
    return {
        "id": tour.id,
        "number": tour.number,
        "league_id": tour.league_id,
        "deadline": tour.deadline,
    }

@router.get(
    "/get_previous_current_next_tour/{league_id}",
    response_model=Optional[dict[str, Optional[TourReadWithType]]]
)
async def get_previous_current_next_tour(league_id: int) -> dict[str, Optional[TourReadWithType]]:
    previous_tour, current_tour, next_tour = await TourService.get_previous_current_next_tour(league_id=league_id)

    def tour_to_read_with_type(tour: Optional[Tour], tour_type: str) -> Optional[TourReadWithType]:
        if not tour:
            return None
        tour_dict = tour_to_dict(tour)
        return TourReadWithType(**tour_dict, type=tour_type)

    return {
        "previous_tour": tour_to_read_with_type(previous_tour, "previous"),
        "current_tour": tour_to_read_with_type(current_tour, "current"),
        "next_tour": tour_to_read_with_type(next_tour, "next"),
    }

@router.post("/start_tour/{tour_id}")
async def start_tour(
    tour_id: int,
    user: User = Depends(get_current_user)
) -> dict:
    """Начать тур и создать SquadTours для следующего тура.
    
    Этот эндпоинт вызывается администратором для начала тура.
    При начале тура создаются SquadTour для следующего тура,
    копируя данные из текущего тура.
    
    TODO: Добавить проверку прав доступа (только для админов)
    
    Args:
        tour_id: ID тура, который нужно начать
    
    Returns:
        Информация о количестве созданных SquadTour
    """
    # TODO: Добавить проверку: if not user.is_admin: raise HTTPException(403)
    
    try:
        result = await SquadService.start_tour_for_all_squads(tour_id=tour_id)
        return {
            "status": "success",
            "message": f"Tour {tour_id} started successfully",
            **result
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start tour: {str(e)}"
        )

@router.post("/finalize_tour/{tour_id}")
async def finalize_tour(
    tour_id: int,
    next_tour_id: Optional[int] = None,
    user: User = Depends(get_current_user)
) -> dict:
    """Финализировать тур и создать snapshots для следующего тура.
    
    Этот эндпоинт должен вызываться администратором после завершения тура.
    Либо может быть автоматизирован через cron/scheduler.
    
    TODO: Добавить проверку прав доступа (только для админов)
    
    Args:
        tour_id: ID завершенного тура
        next_tour_id: ID следующего тура (опционально, определяется автоматически)
    
    Returns:
        Информация о количестве обработанных сквадов
    """
    # TODO: Добавить проверку: if not user.is_admin: raise HTTPException(403)
    
    try:
        # If next_tour_id is not provided, find it automatically
        if next_tour_id is None:
            from app.tours.services import TourService
            tour = await TourService.find_one(tour_id)
            if not tour:
                raise HTTPException(status_code=404, detail="Tour not found")
            
            # Find the next tour by league and number
            tours = await TourService.find_all_by_league(tour.league_id)
            sorted_tours = sorted(tours, key=lambda t: t.number)
            
            current_index = next((i for i, t in enumerate(sorted_tours) if t.id == tour_id), None)
            if current_index is None:
                raise HTTPException(status_code=404, detail="Current tour not found in league")
            
            if current_index + 1 < len(sorted_tours):
                next_tour_id = sorted_tours[current_index + 1].id
            else:
                raise HTTPException(status_code=400, detail="No next tour available")
        
        result = await SquadService.finalize_tour_for_all_squads(
            tour_id=tour_id,
            next_tour_id=next_tour_id
        )
        return {
            "status": "success",
            "message": f"Tour {tour_id} finalized, created snapshots for tour {next_tour_id}",
            **result
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to finalize tour: {str(e)}"
        )
