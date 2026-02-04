from typing import List

from sqlalchemy import Column, ForeignKey, Integer, Table
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

user_league_squads = Table(
    "user_league_squads",
    Base.metadata,
    Column("squad_id", Integer, ForeignKey("squads.id"), primary_key=True),
    Column("user_league_id", Integer, ForeignKey("user_leagues.id"), primary_key=True),
)

commercial_league_squads = Table(
    "commercial_league_squads",
    Base.metadata,
    Column("squad_id", Integer, ForeignKey("squads.id"), primary_key=True),
    Column("commercial_league_id", Integer, ForeignKey("commercial_leagues.id"), primary_key=True),
)

class Squad(Base):
    __tablename__ = "squads"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    league_id: Mapped[int] = mapped_column(ForeignKey("leagues.id"), nullable=False)
    fav_team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), nullable=False)

    fav_team: Mapped["Team"] = relationship(back_populates="squads")
    user: Mapped["User"] = relationship(back_populates="squads")
    league: Mapped["League"] = relationship(back_populates="squads")
    tour_history: Mapped[List["SquadTour"]] = relationship(
        back_populates="squad", cascade="all, delete-orphan"
    )
    used_boosts: Mapped[List["Boost"]] = relationship(back_populates="squad")

    user_leagues: Mapped[List["UserLeague"]] = relationship(
        secondary=user_league_squads, back_populates="squads"
    )
    commercial_leagues: Mapped[List["CommercialLeague"]] = relationship(
        secondary=commercial_league_squads, back_populates="squads"
    )

    def __repr__(self):
        return self.name


