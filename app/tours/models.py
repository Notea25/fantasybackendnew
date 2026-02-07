from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import Column, ForeignKey, Table, UniqueConstraint, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


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
    Column(
        "commercial_league_id",
        ForeignKey("commercial_leagues.id"),
        primary_key=True,
    ),
)


class Tour(Base):
    __tablename__ = "tours"
    id: Mapped[int] = mapped_column(primary_key=True)
    number: Mapped[int]
    league_id: Mapped[int] = mapped_column(ForeignKey("leagues.id"))
    deadline: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    is_started: Mapped[bool] = mapped_column(default=False, server_default="false")
    is_finalized: Mapped[bool] = mapped_column(default=False, server_default="false")

    __table_args__ = (
        UniqueConstraint(
            "league_id", "number", name="unique_tour_number_per_league"
        ),
    )

    league: Mapped["League"] = relationship(back_populates="tours")

    user_leagues: Mapped[list["UserLeague"]] = relationship(
        secondary=user_league_tours, back_populates="tours"
    )
    commercial_leagues: Mapped[list["CommercialLeague"]] = relationship(
        secondary=commercial_league_tours, back_populates="tours"
    )

    matches: Mapped[list["Match"]] = relationship(
        back_populates="tour",
        cascade="all, delete-orphan",
    )
    boosts: Mapped[list["Boost"]] = relationship(back_populates="tour")
    squads: Mapped[list["SquadTour"]] = relationship(
        back_populates="tour", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"Tour {self.number}"
