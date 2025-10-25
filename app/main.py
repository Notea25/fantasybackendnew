import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqladmin import Admin

# from app.admin.view import (ClubAdmin, CompetitionAdmin, PlayerAdmin,
#                             PositionAdmin, SportTypeAdmin, TeamAdmin,
#                             UserAdmin)
from app.leagues.router import router as leagues_router
from app.teams.router import router as teams_router
from app.config import settings
from app.database import engine
from app.matches.router import router as matches_router
from app.players.router import router as players_router
# from app.positions.router import router as positions_router
# from app.sport_types.router import router as sport_types_router
# from app.teams.router import router as teams_router
from app.users.router import router as users_router

# Настройка логирования
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)

app = FastAPI()

# CORS настройки
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене замените на конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users_router)
app.include_router(leagues_router)
app.include_router(teams_router)
app.include_router(matches_router)
app.include_router(players_router)
# # app.include_router(teams_router)
# app.include_router(positions_router)
# app.include_router(sport_types_router)

# admin = Admin(app, engine)
# admin.add_view(PositionAdmin)
# admin.add_view(SportTypeAdmin)
# admin.add_view(UserAdmin)
# admin.add_view(ClubAdmin)
# admin.add_view(CompetitionAdmin)
# admin.add_view(PlayerAdmin)
# admin.add_view(TeamAdmin)
