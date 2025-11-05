from typing import List
from pydantic import BaseModel, ConfigDict

class PlayerInSquadSchema(BaseModel):
    id: int
    name: str
    age: int
    number: int
    position: str
    photo: str
    team_id: int
    market_value: int
    sport: int
    league_id: int
    points: int

class SquadRead(BaseModel):
    id: int
    name: str
    budget: int
    replacements: int
    user_id: int
    league_id: int
    points: int = 0
    players: List[PlayerInSquadSchema] = []
    bench_players: List[PlayerInSquadSchema] = []
    model_config = ConfigDict(from_attributes=True)

class PlayerInSquadUpdateSchema(BaseModel):
    player_id: int
    is_bench: bool = False

class UpdateSquadPlayersSchema(BaseModel):
    main_player_ids: List[int]
    bench_player_ids: List[int]
