import logging

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from sqladmin import Admin
from starlette.middleware.sessions import SessionMiddleware

from app.admin.auth import AdminAuth
from app.admin.utils_view import UtilsView
from app.admin.view import (
    BoostAdmin,
    ClubLeagueAdmin,
    CommercialLeagueAdmin,
    LeagueAdmin,
    MatchAdmin,
    PlayerAdmin,
    PlayerMatchStatsAdmin,
    SquadAdmin,
    SquadTourAdmin,
    TeamAdmin,
    TourAdmin,
    TourMatchesAdmin,
    UserAdmin,
    UserLeagueAdmin,
)
from app.boosts.router import router as boosts_router
from app.config import settings
from app.custom_leagues.club_league.router import router as club_leagues_router
from app.custom_leagues.commercial_league.router import (
    router as commercial_leagues_router,
)
from app.custom_leagues.user_league.router import router as user_leagues_router
from app.database import engine
from app.leagues.router import router as leagues_router
from app.matches.router import router as matches_router
from app.player_match_stats.router import router as player_stats_router
from app.players.router import router as players_router
from app.squads.router import router as squads_router
from app.squad_tours.router import router as squad_tours_router
from app.teams.router import router as teams_router
from app.tours.router import router as tours_router
from app.users.router import router as users_router
from app.utils.router import router as utils_router

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)

app = FastAPI()

# if settings.MODE == "DEVFRONT":
#     app.add_middleware(
#         CORSMiddleware,
#         allow_origins=[
#             "https://014afc12-930d-4917-a39f-0e32b2583b24.lovableproject.com",
#               "https://tele-mini-sparkle.vercel.app"
#         ],
#         allow_credentials=True,
#         allow_methods=["*"],
#         allow_headers=["*"],
#     )
#
#     @app.middleware("http")
#     async def check_origin(request: Request, call_next):
#         allowed_origin = (
#             "https://014afc12-930d-4917-a39f-0e32b2583b24.lovableproject.com",
#             "https://tele-mini-sparkle.vercel.app"
#         )
#         if (request.url.path.startswith("/api") or
#                 request.url.path == "/docs") and \
#                 request.headers.get("origin") != allowed_origin:
#             raise HTTPException(
#                 status_code=403,
#                 detail="Forbidden: Access only from React app"
#             )
#         return await call_next(request)

app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY)

app.include_router(utils_router, prefix="/api")
app.include_router(users_router, prefix="/api")
app.include_router(leagues_router, prefix="/api")
app.include_router(teams_router, prefix="/api")
app.include_router(tours_router, prefix="/api")
app.include_router(matches_router, prefix="/api")
app.include_router(players_router, prefix="/api")
app.include_router(player_stats_router, prefix="/api")
app.include_router(players_router, prefix="/api")
app.include_router(squads_router, prefix="/api")
app.include_router(squad_tours_router, prefix="/api")
app.include_router(boosts_router, prefix="/api")
app.include_router(commercial_leagues_router, prefix="/api")
app.include_router(club_leagues_router, prefix="/api")

authentication_backend = AdminAuth()
admin = Admin(app, engine, authentication_backend=authentication_backend)

admin.add_view(UserAdmin)
admin.add_view(LeagueAdmin)
admin.add_view(MatchAdmin)
admin.add_view(PlayerAdmin)
admin.add_view(SquadAdmin)
admin.add_view(SquadTourAdmin)
admin.add_view(BoostAdmin)
admin.add_view(TeamAdmin)
admin.add_view(PlayerMatchStatsAdmin)
admin.add_view(TourAdmin)
admin.add_view(UserLeagueAdmin)
admin.add_view(CommercialLeagueAdmin)
admin.add_view(ClubLeagueAdmin)
admin.add_view(UtilsView)
admin.add_view(TourMatchesAdmin)