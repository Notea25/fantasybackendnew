from typing import Optional
from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from enum import Enum

class PlayerInSquadSchema(BaseModel):
    id: int
    name: str
    age: int
    number: Optional[int] = Field(default=None)
    position: str
    photo: str
    team_id: int
    market_value: int
    sport: int
    league_id: int
    points: int = Field(default=0)
    model_config = ConfigDict(from_attributes=True)

class SquadRead(BaseModel):
    id: int
    name: str
    budget: int
    replacements: int
    user_id: int
    league_id: int
    points: int = 0
    fav_team_id: int
    available_boosts: int
    current_tour_id: Optional[int] = None
    players: list[PlayerInSquadSchema] = []
    bench_players: list[PlayerInSquadSchema] = []
    model_config = ConfigDict(from_attributes=True)

class SquadTourSchema(BaseModel):
    id: int
    tour_id: int
    is_current: bool
    used_boost: Optional[str] = None
    points: int
    main_players: list[PlayerInSquadSchema] = []
    bench_players: list[PlayerInSquadSchema] = []
    model_config = ConfigDict(from_attributes=True)

class SquadWithHistorySchema(SquadRead):
    tour_history: list[SquadTourSchema] = []

class SquadCreate(BaseModel):
    name: str
    league_id: int
    fav_team_id: int

class UpdateSquadPlayersSchema(BaseModel):
    main_player_ids: list[int]
    bench_player_ids: list[int]
