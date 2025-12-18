from fastapi import APIRouter, Depends
from app.squads.schemas import SquadRead, PlayerInSquadUpdateSchema, UpdateSquadPlayersSchema, SquadCreate
from app.squads.services import SquadService
from app.users.dependencies import get_current_user
from app.users.models import User
from app.utils.exceptions import ResourceNotFoundException, FailedOperationException

router = APIRouter(prefix="/squads", tags=["Squads"])

@router.post("/create")
async def create_squad(squad_data: SquadCreate, user: User = Depends(get_current_user)) -> SquadRead:
    squad = await SquadService.create_squad(name=squad_data.name, user_id=user.id, league_id=squad_data.league_id,
                                            fav_team_id=squad_data.fav_team_id)

    squad = await SquadService.find_one_or_none_with_relations(id=squad.id)
    return squad

@router.get("/list_squads")
async def list_squads() -> list[SquadRead]:
    squads = await SquadService.find_all_with_relations()
    return squads

@router.get("/my_squads")
async def list_users_squads(user: User = Depends(get_current_user)) -> list[SquadRead]:
    squads = await SquadService.find_filtered_with_relations(user_id=user.id)
    return squads

@router.get("/get_squad_{squad_id}")
async def get_squad(squad_id: int, user: User = Depends(get_current_user)) -> SquadRead:
    squad = await SquadService.find_one_or_none_with_relations(id=squad_id, user_id=user.id)
    if not squad:
        raise ResourceNotFoundException()
    return squad

@router.put("/update_players/{squad_id}")
async def update_squad_players(
    squad_id: int, players_data: UpdateSquadPlayersSchema,  user: User = Depends(get_current_user)):
    try:
        squad = await SquadService.update_squad_players(
            squad_id=squad_id,
            main_player_ids=players_data.main_player_ids,
            bench_player_ids=players_data.bench_player_ids
        )
        return {"status": "success", "message": "Squad players updated", "squad": squad}
    except Exception as e:
        raise FailedOperationException(msg=str(e))
