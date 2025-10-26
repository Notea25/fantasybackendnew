import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from sqladmin import Admin
# from app.admin.view import (ClubAdmin, CompetitionAdmin, PlayerAdmin,
#                             PositionAdmin, SportTypeAdmin, TeamAdmin,
#                             UserAdmin)

from app.leagues.router import router as leagues_router
from app.teams.router import router as teams_router
from app.matches.router import router as matches_router
from app.players.router import router as players_router
from app.player_match_stats.router import router as player_match_stats_router
from app.squads.router import router as squads_router
from app.users.router import router as users_router

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], #dev mode
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users_router)
app.include_router(leagues_router)
app.include_router(teams_router)
app.include_router(matches_router)
app.include_router(players_router)
app.include_router(player_match_stats_router)
app.include_router(squads_router)


# admin = Admin(app, engine)
# admin.add_view(PositionAdmin)
# admin.add_view(SportTypeAdmin)
# admin.add_view(UserAdmin)
# admin.add_view(ClubAdmin)
# admin.add_view(CompetitionAdmin)
# admin.add_view(PlayerAdmin)
# admin.add_view(TeamAdmin)
