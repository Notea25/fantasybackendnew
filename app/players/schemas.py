from typing import Optional

from pydantic import BaseModel

class PlayerSchema(BaseModel):
    id: int
    name: str
    age: Optional[int]
    number: Optional[int]
    position: Optional[str]
    photo: Optional[str]
    team_id: int
    market_value: Optional[int]
    sport: int
    league_id: int

    class Config:
        from_attributes = True
