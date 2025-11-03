from pydantic import BaseModel

class PlayerSchema(BaseModel):
    id: int
    name: str
    age: int
    number: int | None = None
    position: str | None = None
    photo: str | None = None
    team_id: int
    market_value: int | None = None
    sport: int
    league_id: int

    class Config:
        from_attributes = True
