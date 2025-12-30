import logging
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from sqladmin import Admin

from app.database import engine
from app.admin.auth import AdminAuth
from app.admin.view import (
    UserAdmin, LeagueAdmin, MatchAdmin, PlayerAdmin,
    SquadAdmin, TeamAdmin, PlayerMatchStatsAdmin,
    TourAdmin, CustomLeagueAdmin, SquadTourAdmin, BoostAdmin
)
from app.leagues.router import router as leagues_router
from app.teams.router import router as teams_router
from app.matches.router import router as matches_router
from app.players.router import router as players_router
from app.player_match_stats.router import router as player_stats_router
from app.squads.router import router as squads_router
from app.boosts.router import router as boosts_router
from app.users.router import router as users_router
from app.utils.router import router as utils_router
from app.tours.router import router as tours_router
from app.custom_leagues.router import router as custom_leagues_router
from app.config import settings

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)

app = FastAPI()

# Middleware для CORS (только для React-приложения)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Замените на домен вашего React-приложения
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware для сессий (для SQLAdmin)
app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY)

# Middleware для проверки Origin (только для API)
@app.middleware("http")
async def check_origin(request: Request, call_next):
    allowed_origin = "http://localhost:3000"  # Замените на домен вашего React-приложения
    if request.url.path.startswith("/api") and request.headers.get("origin") != allowed_origin:
        raise HTTPException(status_code=403, detail="Forbidden: Access only from React app")

    return await call_next(request)

# Подключение всех роутеров
app.include_router(utils_router, prefix="/api")
app.include_router(users_router, prefix="/api")
app.include_router(leagues_router, prefix="/api")
app.include_router(teams_router, prefix="/api")
app.include_router(tours_router, prefix="/api")
app.include_router(matches_router, prefix="/api")
app.include_router(players_router, prefix="/api")
app.include_router(player_stats_router, prefix="/api")
app.include_router(squads_router, prefix="/api")
app.include_router(boosts_router, prefix="/api")
app.include_router(custom_leagues_router, prefix="/api")

# Настройка SQLAdmin с аутентификацией
authentication_backend = AdminAuth()
admin = Admin(app, engine, authentication_backend=authentication_backend)

# Добавление всех вьюх
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
