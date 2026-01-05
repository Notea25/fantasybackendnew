from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, Table, Column, Integer
from app.database import Base
from sqlalchemy import UniqueConstraint
from app.custom_leagues.models import custom_league_tours

tour_matches_association = Table(
    "tour_matches_association",
    Base.metadata,
    Column("tour_id", ForeignKey("tours.id"), primary_key=True),
    Column("match_id", ForeignKey("matches.id"), primary_key=True),
    extend_existing=True,
)

class TourMatchAssociation(Base):
    __table__ = tour_matches_association

    tour: Mapped["Tour"] = relationship("Tour", back_populates="matches_association")
    match: Mapped["Match"] = relationship("Match", back_populates="tours_association")

class Tour(Base):
    __tablename__ = "tours"
    id: Mapped[int] = mapped_column(primary_key=True)
    number: Mapped[int] = mapped_column(Integer)
    league_id: Mapped[int] = mapped_column(ForeignKey("leagues.id"))

    __table_args__ = (
        UniqueConstraint("league_id", "number", name="unique_tour_number_per_league"),
    )

    league: Mapped["League"] = relationship(back_populates="tours")
    custom_leagues: Mapped[list["CustomLeague"]] = relationship(secondary=custom_league_tours, back_populates="tours")
    matches_association: Mapped[list["TourMatchAssociation"]] = relationship(
        back_populates="tour",
        cascade="all, delete-orphan",
    )
    boosts: Mapped[list["Boost"]] = relationship(back_populates="tour")
    squads: Mapped[list["SquadTour"]] = relationship(back_populates="tour")

    @property
    def start_date(self) -> Optional[datetime]:
        if not self.matches:
            return None
        return min(match.date for match in self.matches)

    @property
    def end_date(self) -> Optional[datetime]:
        if not self.matches:
            return None
        return max(match.date for match in self.matches) + timedelta(hours=2)

    @property
    def deadline(self) -> Optional[datetime]:
        if not self.start_date:
            return None
        return self.start_date - timedelta(hours=2)

    def __repr__(self):
        return f"Tour {self.number}"
