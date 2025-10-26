from pydantic import BaseModel

class LeagueSchema(BaseModel):
    id: int
    name: str
    sport: int

    class Config:
        from_attributes = True
