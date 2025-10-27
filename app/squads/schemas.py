from typing import List, Optional
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

class SquadRead(BaseModel):
    id: int
    name: str
    budget: int
    replacements: int
    user_id: int
    league_id: int
    players: List[PlayerInSquadSchema] = []
    bench_players: List[PlayerInSquadSchema] = []

    model_config = ConfigDict(from_attributes=True)
