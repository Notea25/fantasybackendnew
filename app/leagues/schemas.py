from pydantic import BaseModel, ConfigDict


class LeagueBase(BaseModel):
    name: str


class LeagueCreate(LeagueBase):
    pass


class LeagueRead(LeagueBase):
    id: int
    sport: int

    model_config = ConfigDict(from_attributes=True)
