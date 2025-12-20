from typing import List
from sqlalchemy import ForeignKey, Table, Column
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

tour_matches_association = Table(
    "tour_matches_association",
    Base.metadata,
    Column("tour_id", ForeignKey("tours.id"), primary_key=True),
    Column("match_id", ForeignKey("matches.id"), primary_key=True),
    extend_existing=True,
)

class Tour(Base):
    __tablename__ = "tours"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    league_id: Mapped[int] = mapped_column(ForeignKey("leagues.id"))

    league: Mapped["League"] = relationship(back_populates="tours")
    matches: Mapped[List["Match"]] = relationship(
        secondary=tour_matches_association,
        back_populates="tours"
    )

    def __repr__(self):
        return f"Tour {self.name}"
