from pydantic import BaseModel, ConfigDict


class PositionBase(BaseModel):
    name: str

class PositionCreate(PositionBase):
    pass

class PositionRead(PositionBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


class SportTypeBase(BaseModel):
    name: str

class SportTypeCreate(SportTypeBase):
    pass

class SportTypeRead(SportTypeBase):
    id: int

    model_config = ConfigDict(from_attributes=True)