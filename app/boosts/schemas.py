from pydantic import BaseModel
from datetime import datetime
from enum import Enum

class BoostType(str, Enum):
    BENCH_BOOST = "bench_boost"
    TRIPLE_CAPTAIN = "triple_captain"
    TRANSFERS_PLUS = "transfers_plus"
    GOLD_TOUR = "gold_tour"
    DOUBLE_BET = "double_bet"

class BoostBase(BaseModel):
    squad_id: int
    tour_id: int
    type: BoostType

class BoostCreate(BoostBase):
    pass

class Boost(BoostBase):
    id: int
    used_at: datetime

    class Config:
        from_attributes = True

class BoostInfo(BaseModel):
    type: BoostType
    description: str
    available: bool
