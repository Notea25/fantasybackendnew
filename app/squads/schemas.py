from pydantic import BaseModel, ConfigDict
from typing import Optional, List

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
    main_player_ids: List[int] = []
    bench_player_ids: List[int] = []

    model_config = ConfigDict(from_attributes=True)

class SquadCreate(BaseModel):
    name: str
    league_id: int
    fav_team_id: int
    main_player_ids: List[int]
    bench_player_ids: List[int]

class UpdateSquadPlayersSchema(BaseModel):
    main_player_ids: List[int]
    bench_player_ids: List[int]

class SquadTourSchema(BaseModel):
    id: int
    tour_id: int
    is_current: bool
    used_boost: Optional[str] = None
    points: int
    main_player_ids: List[int] = []
    bench_player_ids: List[int] = []

    model_config = ConfigDict(from_attributes=True)

class ReplacementInfo(BaseModel):
    available_replacements: int
    budget: int
    current_players_cost: int

    model_config = ConfigDict(from_attributes=True)
