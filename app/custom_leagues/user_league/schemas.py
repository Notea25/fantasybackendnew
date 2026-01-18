from typing import Optional

from pydantic import BaseModel


class UserLeagueSchema(BaseModel):
    id: int
    name: str
    league_id: int
    creator_id: int

    class Config:
        from_attributes = True

class UserLeagueWithStatsSchema(BaseModel):
    user_league_id: int
    user_league_name: str
    total_players: int
    squad_place: int
    is_creator: bool
    squad_id: int
    squad_name: str

    class Config:
        from_attributes = True


class UserLeagueCreateSchema(BaseModel):
    name: str
    league_id: int


    class Config:
        from_attributes = True