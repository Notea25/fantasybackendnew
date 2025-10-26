from fastapi import APIRouter, Depends, HTTPException
from app.squads.schemas import SquadCreate, SquadRead, SquadSchema
from app.squads.services import SquadService
from app.users.dependencies import get_current_user
from app.users.models import User

router = APIRouter(prefix="/squads", tags=["Squads"])

@router.get("/list_squads")
async def list_squads() -> list[SquadRead]:
    return await SquadService.find_all()

@router.post("/create")
async def create_squad(
    squad: SquadSchema, user: User = Depends(get_current_user)
) -> SquadRead:
    squad.user_id = user.id
    return await SquadService.add_one(data=squad.model_dump())

@router.get("/my_squads")
async def list_users_squads(user: User = Depends(get_current_user)) -> list[SquadRead]:
    return await SquadService.find_filtered(user_id=user.id)

@router.get("/{squad_id}")
async def get_squad(squad_id: int, user: User = Depends(get_current_user)) -> SquadRead:
    squad = await SquadService.find_one_or_none(id=squad_id, user_id=user.id)
    if not squad:
        raise HTTPException(status_code=404, detail="Squad not found")
    return squad

@router.put("/{squad_id}")
async def update_squad(
    squad_id: int, squad: SquadSchema, user: User = Depends(get_current_user)
) -> SquadRead:
    squad.user_id = user.id
    return await SquadService.update(squad_id, data=squad.model_dump())

@router.delete("/{squad_id}")
async def delete_squad(squad_id: int, user: User = Depends(get_current_user)):
    await SquadService.delete(id=squad_id, user_id=user.id)
    return {"status": "deleted"}
