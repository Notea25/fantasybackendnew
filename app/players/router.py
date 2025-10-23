from fastapi import APIRouter

from app.exceptions import ResourceNotFoundException
from app.players.schemas import PlayerRead
from app.players.services import PlayerService

router = APIRouter(prefix="/players", tags=["Players"])


@router.get("/all")
async def list_players() -> list[PlayerRead]:
    return await PlayerService.find_all()


@router.get("/player_{player_id}")
async def get_player(player_id: int) -> PlayerRead:
    res = await PlayerService.find_one_or_none(id=player_id)
    if not res:
        raise ResourceNotFoundException
    return res


@router.get("/team_{team_id}")
async def get_player_by_team_id(team_id: int) -> list[PlayerRead]:
    res = await PlayerService.find_filtered(team_id=team_id)
    if not res:
        raise ResourceNotFoundException
    return res


# @router.get("/players_with-stats", response=list[PlayerSchema])
# def get_all_players_with_stats(request):
#     return PlayerService.all_players_with_stats()
#
#
# @router.get("/player/{player_id}/stats", response=PlayerSchema)
# def get_player_with_stats(request, player_id: str):
#     return PlayerService.find_player_and_stats(player_id)
#
#
# @router.post("/fetched", response=PlayerSchema)
# def create_player(request, payload: PlayerSchema):
#     return PlayerService.create(**payload.dict())
#
#
# @router.put("/fetched/{player_id}", response=PlayerSchema)
# def update_player(request, player_id: str, payload: PlayerSchema):
#     return PlayerService.update(player_id, **payload.dict())
#
#
# @router.delete("/fetched/{player_id}")
# def delete_player(request, player_id: str):
#     return PlayerService.delete(player_id)


# @router.post("/fetch_players")
# def fetch_players():
#     url = "http://localhost:7000/players/all_players"
#     response = requests.get(url)
#     if response.status_code == 200:
#         players_data = response.json()
#         for player_data in players_data:
#             player, created = Player.objects.update_or_create(
#                 id=player_data["id"],
#                 defaults={
#                     "name": player_data["name"],
#                     "position": player_data["position"],
#                     "age": player_data["age"],
#                     "height": player_data["height"],
#                     "market_value": player_data["market_value"],
#                     "club_id": player_data["club_id"]
#                 }
#             )
#         return {"success": True, "message": "Players fetched and added to the database."}
#     else:
#         return {"success": False, "message": "Failed to fetch fetched."}
