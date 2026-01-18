from sqlalchemy import Column, Integer,  ForeignKey, Table
from sqlalchemy.orm import relationship, Mapped, mapped_column
from app.database import Base

user_league_tours = Table(
    "user_league_tours",
    Base.metadata,
    Column("user_league_id", Integer, ForeignKey("user_leagues.id"), primary_key=True),
    Column("tour_id", Integer, ForeignKey("tours.id"), primary_key=True),
    extend_existing=True,
)

user_league_squads = Table(
    "user_league_squads",
    Base.metadata,
    Column("user_league_id", Integer, ForeignKey("user_leagues.id"), primary_key=True),
    Column("squad_id", Integer, ForeignKey("squads.id"), primary_key=True),
    extend_existing=True,
)

class UserLeague(Base):
    __tablename__ = "user_leagues"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    league_id: Mapped[int] = mapped_column(ForeignKey("leagues.id"))
    creator_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)

    league: Mapped["League"] = relationship(back_populates="user_leagues")
    creator: Mapped["User"] = relationship(back_populates="user_leagues")
    tours: Mapped[list["Tour"]] = relationship(secondary=user_league_tours, back_populates="user_leagues")
    squads: Mapped[list["Squad"]] = relationship(secondary=user_league_squads, back_populates="user_leagues")
