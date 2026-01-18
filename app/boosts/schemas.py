from enum import Enum

from pydantic import BaseModel


class BoostType(str, Enum):
    BENCH_BOOST = "bench_boost"
    TRIPLE_CAPTAIN = "triple_captain"
    TRANSFERS_PLUS = "transfers_plus"
    GOLD_TOUR = "gold_tour"
    DOUBLE_BET = "double_bet"


class BoostCreate(BaseModel):
    squad_id: int
    tour_id: int
    type: BoostType
