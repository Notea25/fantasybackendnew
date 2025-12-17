from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, conint

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
    budget: int #conint(ge=0)
    replacements: int
    user_id: int
    league_id: int
    points: int = 0
    fav_team_id: int
    players: list[PlayerInSquadSchema] = []
    bench_players: list[PlayerInSquadSchema] = []
    model_config = ConfigDict(from_attributes=True)



class SquadCreate(BaseModel):
    name: str
    league_id: int
    fav_team_id: int

class PlayerInSquadUpdateSchema(BaseModel):
    player_id: int
    is_bench: bool = False

class UpdateSquadPlayersSchema(BaseModel):
    main_player_ids: list[int]
    bench_player_ids: list[int]
