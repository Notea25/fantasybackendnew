from typing import Optional, List
from collections import defaultdict
from fastapi import HTTPException
from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from app.players.schemas import PlayerSchema


class SquadBase(BaseModel):
    name: str
    competition_id: int
    budget: int = 100_000
    replacements: int = 3
    user_id: Optional[int] = None

class SquadCreate(SquadBase):
    players: List[PlayerSchema] = []
    bench_players: List[PlayerSchema] = []

    @field_validator("players", "bench_players", mode="before")
    def check_player_type(cls, v):
        if isinstance(v, list):
            for item in v:
                if not isinstance(item, dict):
                    raise ValueError("Each item must be a PlayerSchema")
        return v

class SquadSchema(SquadCreate):
    @model_validator(mode="after")
    def validate_players(self):
        all_players = self.players + self.bench_players

        if len(all_players) > 15:
            raise HTTPException(
                status_code=400,
                detail="A squad cannot have more than 15 players."
            )

        total_market_value = sum(player.market_value for player in all_players)
        if total_market_value > self.budget:
            raise HTTPException(
                status_code=400,
                detail=f"The total market value of all players cannot exceed {self.budget}."
            )

        positions = {player.position for player in all_players}
        required_positions = {"Goalkeeper", "Defender", "Midfielder", "Striker"}
        if not required_positions.issubset(positions):
            raise HTTPException(
                status_code=400,
                detail="The squad must have at least one player in each role: Goalkeeper, Defender, Midfielder, Striker."
            )

        team_count = defaultdict(int)
        for player in all_players:
            team_count[player.team_id] += 1
            if team_count[player.team_id] > 3:
                raise HTTPException(
                    status_code=400,
                    detail=f"A squad cannot have more than 3 players from the same team (team_id: {player.team_id})."
                )
        return self

class SquadRead(BaseModel):
    id: int
    name: str
    competition_id: int
    budget: int
    replacements: int
    user_id: int
    players: List[PlayerSchema] = []
    bench_players: List[PlayerSchema] = []

    model_config = ConfigDict(from_attributes=True)

class SquadSchemaGet(SquadRead):
    pass
