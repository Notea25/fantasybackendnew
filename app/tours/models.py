from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, Table, Column, UniqueConstraint
from app.database import Base

# Промежуточные таблицы для связей с различными типами лиг
user_league_tours = Table(
    "user_league_tours",
    Base.metadata,
    Column("tour_id", ForeignKey("tours.id"), primary_key=True),
    Column("user_league_id", ForeignKey("user_leagues.id"), primary_key=True),
)

commercial_league_tours = Table(
    "commercial_league_tours",
    Base.metadata,
    Column("tour_id", ForeignKey("tours.id"), primary_key=True),
    Column("commercial_league_id", ForeignKey("commercial_leagues.id"), primary_key=True),
)

club_league_tours = Table(
    "club_league_tours",
    Base.metadata,
    Column("tour_id", ForeignKey("tours.id"), primary_key=True),
    Column("club_league_id", ForeignKey("club_leagues.id"), primary_key=True),
)

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
    number: Mapped[int]
    league_id: Mapped[int] = mapped_column(ForeignKey("leagues.id"))

    __table_args__ = (
        UniqueConstraint("league_id", "number", name="unique_tour_number_per_league"),
    )

    league: Mapped["League"] = relationship(back_populates="tours")

    # Связи с различными типами лиг
    user_leagues: Mapped[list["UserLeague"]] = relationship(secondary=user_league_tours, back_populates="tours")
    commercial_leagues: Mapped[list["CommercialLeague"]] = relationship(secondary=commercial_league_tours, back_populates="tours")
    club_leagues: Mapped[list["ClubLeague"]] = relationship(secondary=club_league_tours, back_populates="tours")

    matches_association: Mapped[list["TourMatchAssociation"]] = relationship(
        back_populates="tour",
        cascade="all, delete-orphan",
    )
    boosts: Mapped[list["Boost"]] = relationship(back_populates="tour")
    squads: Mapped[list["SquadTour"]] = relationship(back_populates="tour")

    @property
    def start_date(self) -> Optional[datetime]:
        if not self.matches_association:
            return None
        return min(association.match.date for association in self.matches_association)

    @property
    def end_date(self) -> Optional[datetime]:
        if not self.matches_association:
            return None
        return max(association.match.date for association in self.matches_association) + timedelta(hours=2)

    @property
    def deadline(self) -> Optional[datetime]:
        if not self.start_date:
            return None
        return self.start_date - timedelta(hours=2)

    def __repr__(self):
        return f"Tour {self.number}"
