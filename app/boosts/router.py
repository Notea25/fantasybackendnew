from fastapi import APIRouter, Depends
from app.boosts.schemas import BoostCreate
from app.boosts.services import BoostService
from app.users.dependencies import get_current_user
from app.utils.exceptions import FailedOperationException

router = APIRouter(prefix="/boosts", tags=["Boosts"])

@router.post("/apply")
async def apply_boost(
    boost_data: BoostCreate,
    user: dict = Depends(get_current_user)
):
    try:
        boost = await BoostService.apply_boost(
            squad_id=boost_data.squad_id,
            tour_id=boost_data.tour_id,
            boost_type=boost_data.type
        )
        return {"status": "success", "message": "Boost applied", "boost": boost}
    except FailedOperationException as e:
        raise e

@router.get("/available/{squad_id}/{tour_id}")
async def get_available_boosts(
    squad_id: int,
    tour_id: int,
    user: dict = Depends(get_current_user)
):
    return await BoostService.get_available_boosts(squad_id, tour_id)

@router.get("/squad/{squad_id}")
async def get_squad_boosts(
    squad_id: int,
    user: dict = Depends(get_current_user)
):
    return await BoostService.get_squad_boosts(squad_id)
