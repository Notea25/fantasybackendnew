from typing import Optional
from pydantic import BaseModel, ConfigDict, Field
from enum import Enum

class BoostType(str, Enum):
    BENCH_BOOST = "bench_boost"
    TRIPLE_CAPTAIN = "triple_captain"
    TRANSFERS_PLUS = "transfers_plus"
    GOLD_TOUR = "gold_tour"
    DOUBLE_BET = "double_bet"

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
    used_boost: Optional[BoostType] = None
    points: int
    main_players: list[PlayerInSquadSchema] = []
    bench_players: list[PlayerInSquadSchema] = []
    model_config = ConfigDict(from_attributes=True)

class SquadWithHistorySchema(SquadRead):
    tour_history: list[SquadTourSchema] = []
    used_boosts: list[BoostType] = []

class SquadCreate(BaseModel):
    name: str
    league_id: int
    fav_team_id: int

class UpdateSquadPlayersSchema(BaseModel):
    main_player_ids: list[int]
    bench_player_ids: list[int]

class BoostInfoSchema(BaseModel):
    type: BoostType
    description: str
    available: bool

class AvailableBoostsSchema(BaseModel):
    available_boosts: int
    used_in_current_tour: bool
    boosts: list[BoostInfoSchema]

class SquadWithBoostsSchema(SquadRead):
    used_boosts: list[dict] = []
    available_boosts: int
    tour_history: list[SquadTourSchema] = []