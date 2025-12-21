import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from sqladmin import Admin

from app.database import engine
from app.admin.view import UserAdmin, LeagueAdmin, MatchAdmin, PlayerAdmin, SquadAdmin, TeamAdmin, \
    PlayerMatchStatsAdmin, \
    TourAdmin, CustomLeagueAdmin, SquadTourAdmin, BoostAdmin

from app.leagues.router import router as leagues_router
from app.teams.router import router as teams_router
from app.matches.router import router as matches_router
from app.players.router import router as players_router
from app.player_match_stats.router import router as player_stats_router
from app.squads.router import router as squads_router
from app.users.router import router as users_router
from app.utils.router import router as utils_router
from app.tours.router import router as tours_router
from app.custom_leagues.router import router as custom_leagues_router

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(utils_router)
app.include_router(users_router)
app.include_router(leagues_router)
app.include_router(teams_router)
app.include_router(tours_router)
app.include_router(matches_router)
app.include_router(players_router)
app.include_router(player_stats_router)
app.include_router(squads_router)
app.include_router(custom_leagues_router)


admin = Admin(app, engine)
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
admin.add_view(CustomLeagueAdmin)
