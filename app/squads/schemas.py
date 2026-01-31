from typing import Optional
from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class PlayerInSquadSchema(BaseModel):
    id: int
    name: str
    position: Optional[str]
    team_id: int
    team_name: str
    team_logo: Optional[str]
    market_value: int
    photo: Optional[str]
    total_points: int = 0  # Сумма очков за все туры
    tour_points: int = 0   # Очки за последний/текущий тур

    model_config = ConfigDict(from_attributes=True)


class SquadReadSchema(BaseModel):
    """Squad metadata only - state moved to SquadTour"""
    id: int
    name: str
    user_id: int
    username: str
    league_id: int
    fav_team_id: int

    model_config = ConfigDict(from_attributes=True)


class SquadCreateSchema(BaseModel):
    name: str
    league_id: int
    fav_team_id: int
    captain_id: int
    vice_captain_id: int
    main_player_ids: list[int]
    bench_player_ids: list[int]


class SquadUpdatePlayersSchema(BaseModel):
    captain_id: Optional[int] = None
    vice_captain_id: Optional[int] = None
    # Для обновления/замены игроков поля могут быть частичными,
    # поэтому делаем списки опциональными.
    main_player_ids: Optional[list[int]] = None
    bench_player_ids: Optional[list[int]] = None


class SquadReplacePlayersResponseSchema(BaseModel):
    status: str
    message: str
    remaining_replacements: int
    squad_tour: "SquadTourHistorySchema"  # Forward reference - defined below
    # Информация о трансферах
    transfers_applied: Optional[int] = None
    free_transfers_used: Optional[int] = None
    paid_transfers: Optional[int] = None
    penalty: Optional[int] = None


class SquadUpdateResponseSchema(BaseModel):
    status: str
    message: str
    squad: SquadReadSchema


class ReplacementInfoSchema(BaseModel):
    available_replacements: int
    budget: int
    current_players_cost: int
    tour_id: int  # Which tour this info is for

    model_config = ConfigDict(from_attributes=True)


class SquadRenameSchema(BaseModel):
    id: int
    name: str
    user_id: int
    league_id: int
    fav_team_id: int

    model_config = ConfigDict(from_attributes=True)


class SquadTourHistorySchema(BaseModel):
    """Complete snapshot of squad state for a tour"""
    tour_id: int
    tour_number: int
    points: int
    penalty_points: int
    used_boost: Optional[str]
    captain_id: Optional[int]
    vice_captain_id: Optional[int]
    budget: int
    replacements: int
    is_finalized: bool
    main_players: list[PlayerInSquadSchema]
    bench_players: list[PlayerInSquadSchema]

    model_config = ConfigDict(from_attributes=True)


class LeaderboardEntrySchema(BaseModel):
    rank: int
    squad_id: int
    squad_name: str
    user_id: int
    username: str
    points: int
    fav_team_id: int

    model_config = ConfigDict(from_attributes=True)


class PublicLeaderboardEntrySchema(BaseModel):
    """Схема для публичного API лидерборда, соответствующая фронтенду.

    Поля:
    - place: порядковое место в туре
    - tour_points: очки за конкретный тур
    - total_points: суммарные очки за все туры
    - penalty_points: штраф за текущий тур
    - total_penalty_points: сумма штрафов за все туры
    """

    place: int
    squad_id: int
    squad_name: str
    user_id: int
    username: str
    tour_points: int
    total_points: int
    penalty_points: int
    total_penalty_points: int

    model_config = ConfigDict(from_attributes=True)


class PublicClubLeaderboardEntrySchema(BaseModel):
    """Лидерборд клубной лиги (po fav_team_id), формат для фронта.

    Используется для эндпоинта /squads/leaderboard/{tour_id}/by-fav-team/{fav_team_id}
    и соответствует типу CustomLeagueLeaderboardEntry на фронтенде.
    """

    place: int
    squad_id: int
    squad_name: str
    user_id: int
    username: str
    tour_points: int
    total_points: int
    penalty_points: int
    total_penalty_points: int
    fav_team_id: int
    fav_team_name: str | None = None

    model_config = ConfigDict(from_attributes=True)
