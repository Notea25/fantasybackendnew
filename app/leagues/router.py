from fastapi import APIRouter

from app.leagues.schemas import LeagueRead
from app.leagues.services import LeagueService
from app.exceptions import ResourceNotFoundException

router = APIRouter(prefix="/leagues", tags=["Leagues"])


@router.get("/all")
async def list_leagues() -> list[LeagueRead]:
    return await LeagueService.find_all()


@router.get(
    "/{league_id}",
)
async def get_leagues(league_id: str) -> LeagueRead:
    res = await LeagueService.find_one_or_none(league_id=league_id)
    if not res:
        raise ResourceNotFoundException
    return res


# @router.get("/sport_type_{sport_type}/")
# async def get_leagues_by_sport_type(sport_type: int) -> list[LeagueRead]:
#     res = await LeagueService.find_filtered(sport_type=sport_type)
#     if not res:
#         raise ResourceNotFoundException
#     return res


# @router.post("/leagues", response=CompetitionSchema, auth=AuthBearer())
# def create_competition(request, payload: CompetitionSchema):
#     user = request.auth
#     payload_dict = payload.dict()
#     payload_dict["creator_id"] = user.id
#     return CompetitionService.create_competition(user, **payload_dict)
#
#
#
# @router.put(
#     "/leagues/{competition_id}", response=CompetitionSchema, auth=AuthBearer(),
# )
# def update_competition(request, competition_id: str, payload: CompetitionSchema):
#     user = request.auth
#     payload_dict = payload.dict()
#     payload_dict["creator_id"] = user.id
#     return CompetitionService.update_competition(competition_id, user, **payload_dict)
#
#
# @router.delete("/leagues/{competition_id}", auth=AuthBearer())
# def delete_competition(request, competition_id: str):
#     user = request.auth
#     return CompetitionService.delete_competition(competition_id, user)


# @router.post("/fetch_competitions")
# def fetch_competitions():
#     url = "http://localhost:7000/competitions"
#     response = requests.get(url)
#     if response.status_code == 200:
#         competitions_data = response.json()
#         for competition_data in competitions_data:
#             competition, created = Competition.objects.update_or_create(
#                 id=competition_data["id"],
#                 defaults={
#                     "name": competition_data["name"],
#                     "season_id": competition_data.get("season_id", "0"),
#                 },
#             )
#         return {"success": True, "message": "Competitions fetched and added to the database."}
#     else:
#         return {"success": False, "message": "Failed to fetch leagues."}
