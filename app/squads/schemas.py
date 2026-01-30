from typing import Optional

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
    id: int
    name: str
    user_id: int
    username: str
    league_id: int
    fav_team_id: int
    budget: int
    replacements: int
    points: int
    captain_id: Optional[int]
    vice_captain_id: Optional[int]
    main_players: list[PlayerInSquadSchema]
    bench_players: list[PlayerInSquadSchema]

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
    squad: SquadReadSchema
    # Информация о трансферах
    transfers_applied: Optional[int] = None
    free_transfers_used: Optional[int] = None
    paid_transfers: Optional[int] = None
    penalty: Optional[int] = None
    new_total_points: Optional[int] = None


class SquadUpdateResponseSchema(BaseModel):
    status: str
    message: str
    squad: SquadReadSchema


class ReplacementInfoSchema(BaseModel):
    available_replacements: int
    budget: int
    current_players_cost: int

    model_config = ConfigDict(from_attributes=True)


class SquadRenameSchema(BaseModel):
    id: int
    name: str
    user_id: int
    league_id: int
    fav_team_id: int
    budget: int
    replacements: int
    captain_id: Optional[int]
    vice_captain_id: Optional[int]

    model_config = ConfigDict(from_attributes=True)


class SquadTourHistorySchema(BaseModel):
    tour_id: int
    tour_number: int
    points: int
    used_boost: Optional[str]
    captain_id: Optional[int]
    vice_captain_id: Optional[int]
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
    """

    place: int
    squad_id: int
    squad_name: str
    user_id: int
    username: str
    tour_points: int
    total_points: int

    model_config = ConfigDict(from_attributes=True)


class PublicClubLeaderboardEntrySchema(BaseModel):
    """Лидерборд клубной лиги (по fav_team_id), формат для фронта.

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
    fav_team_id: int
    fav_team_name: str | None = None

    model_config = ConfigDict(from_attributes=True)
