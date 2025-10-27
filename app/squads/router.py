from fastapi import APIRouter, Depends, HTTPException
from app.squads.schemas import SquadRead
from app.squads.services import SquadService
from app.users.dependencies import get_current_user
from app.users.models import User

router = APIRouter(prefix="/squads", tags=["Squads"])

@router.get("/list_squads")
async def list_squads() -> list[SquadRead]:
    squads = await SquadService.find_all_with_relations()
    return squads

@router.get("/my_squads")
async def list_users_squads(user: User = Depends(get_current_user)) -> list[SquadRead]:
    squads = await SquadService.find_filtered_with_relations(user_id=user.id)
    return squads

@router.get("/{squad_id}")
async def get_squad(squad_id: int, user: User = Depends(get_current_user)) -> SquadRead:
    squad = await SquadService.find_one_or_none_with_relations(id=squad_id, user_id=user.id)
    if not squad:
        raise HTTPException(status_code=404, detail="Squad not found")
    return squad
