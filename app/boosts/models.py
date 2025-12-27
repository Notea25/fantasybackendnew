from sqlalchemy import Column, Integer, ForeignKey, DateTime, Enum
from sqlalchemy.orm import relationship, Mapped, mapped_column
from app.database import Base
from datetime import datetime
from enum import Enum as PyEnum

class BoostType(PyEnum):
    BENCH_BOOST = "bench_boost"
    TRIPLE_CAPTAIN = "triple_captain"
    TRANSFERS_PLUS = "transfers_plus"
    GOLD_TOUR = "gold_tour"
    DOUBLE_BET = "double_bet"

class Boost(Base):
    __tablename__ = "boosts"
    id: Mapped[int] = mapped_column(primary_key=True)
    squad_id: Mapped[int] = mapped_column(ForeignKey("squads.id"))
    tour_id: Mapped[int] = mapped_column(ForeignKey("tours.id"))
    type: Mapped[BoostType]
    used_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    squad: Mapped["Squad"] = relationship(back_populates="used_boosts")
    tour: Mapped["Tour"] = relationship(back_populates="boosts")

    def __repr__(self):
        return f"{self.type.value} for squad {self.squad_id} in tour {self.tour_id}"
