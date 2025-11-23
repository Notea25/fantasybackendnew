from pydantic import BaseModel

class LeagueSchema(BaseModel):
    id: int
    name: str
    logo: str = None
    sport: int

    class Config:
        from_attributes = True
