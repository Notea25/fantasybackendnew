from pydantic import BaseModel, ConfigDict


class PlayerBase(BaseModel):
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


class PlayerCreate(PlayerBase):
    pass


class PlayerRead(PlayerBase):
    pass


    model_config = ConfigDict(from_attributes=True)
