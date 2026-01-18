from pydantic import BaseModel


class ClubLeagueSchema(BaseModel):
    id: int
    name: str
    league_id: int
    team_id: int

    class Config:
        from_attributes = True

class ClubLeagueListSchema(BaseModel):
    id: int
    name: str
    league_id: int
    team_id: int

    class Config:
        from_attributes = True