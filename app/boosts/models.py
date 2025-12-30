from sqlalchemy import Column, Integer, ForeignKey, DateTime, Enum
from sqlalchemy.orm import relationship, Mapped, mapped_column
from app.database import Base
from datetime import datetime


class Boost(Base):
    __tablename__ = "boosts"
    id: Mapped[int] = mapped_column(primary_key=True)
    squad_id: Mapped[int] = mapped_column(ForeignKey("squads.id"))
    tour_id:  Mapped[int] = mapped_column(ForeignKey("tours.id"))
    type: Mapped[str] = mapped_column(default=False)
    used_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    squad: Mapped["Squad"] = relationship(back_populates="used_boosts")
    tour: Mapped["Tour"] = relationship(back_populates="boosts")

    def __repr__(self):
        return f"{self.type.value} for squad {self.squad_id} in tour {self.tour_id}"
