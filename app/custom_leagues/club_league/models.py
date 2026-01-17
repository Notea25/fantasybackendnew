from sqlalchemy import Column, Integer, String, ForeignKey, Table
from sqlalchemy.orm import relationship, Mapped, mapped_column
from app.database import Base

club_league_tours = Table(
    "club_league_tours",
    Base.metadata,
    Column("club_league_id", Integer, ForeignKey("club_leagues.id"), primary_key=True),
    Column("tour_id", Integer, ForeignKey("tours.id"), primary_key=True),
    extend_existing=True,
)

club_league_squads = Table(
    "club_league_squads",
    Base.metadata,
    Column("club_league_id", Integer, ForeignKey("club_leagues.id"), primary_key=True),
    Column("squad_id", Integer, ForeignKey("squads.id"), primary_key=True),
    extend_existing=True,
)

class ClubLeague(Base):
    __tablename__ = "club_leagues"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    league_id: Mapped[int] = mapped_column(ForeignKey("leagues.id"))
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), nullable=False)

    league: Mapped["League"] = relationship(back_populates="club_leagues")
    team: Mapped["Team"] = relationship(back_populates="club_leagues")
    tours: Mapped[list["Tour"]] = relationship(secondary=club_league_tours, back_populates="club_leagues")
    squads: Mapped[list["Squad"]] = relationship(secondary=club_league_squads, back_populates="club_leagues")
