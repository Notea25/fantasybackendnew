from pydantic import BaseModel, ConfigDict


class TeamBase(BaseModel):
    name: str
    league_id: int


class TeamCreate(TeamBase):
    pass


class TeamRead(TeamBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
