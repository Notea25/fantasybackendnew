# from fastapi import APIRouter, Depends
#
# from app.teams.schemas import TeamCreate, TeamRead, TeamSchema
# from app.teams.services import TeamService
# from app.users.dependencies import get_current_user
# from app.users.models import User
#
# router = APIRouter(prefix="/teams", tags=["Teams"])
#
#
# @router.get("/list_teams")
# async def list_teams() -> list[TeamRead]:
#     return await TeamService.find_all()
#
#
# @router.post("/create")
# async def create_team(
#     team: TeamSchema, user: User = Depends(get_current_user)
# ) -> TeamCreate:
#     team.user_id = user.id
#     return await TeamService.add_one(data=team)
#
#
# @router.get("/my_teams")
# async def list_users_teams(user: User = Depends(get_current_user)) -> list[TeamRead]:
#     return await TeamService.find_filtered(user=user)
#
#
# @router.get("/{team_id}")
# async def get_team(team_id: int, user: User = Depends(get_current_user)) -> TeamRead:
#     return await TeamService.find_filtered(id=team_id, user_id=user.id)
#
#
# @router.put("/{team_id}")
# async def update_team(
#     team_id: int, team: TeamSchema, user: User = Depends(get_current_user)
# ) -> TeamCreate:
#     team.user_id = user.id
#     return await TeamService.update(team_id, data=team)
#
#
# @router.delete("/{team_id}")
# async def delete_team(team_id: int, user: User = Depends(get_current_user)):
#     await TeamService.delete(id=team_id)
#     return "deleted"
