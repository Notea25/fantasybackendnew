from pydantic import BaseModel

class PlayerSchema(BaseModel):
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

    class Config:
        from_attributes = True
