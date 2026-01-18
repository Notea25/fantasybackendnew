from sqlalchemy import Column, Integer, String, ForeignKey, Table, DateTime
from sqlalchemy.orm import relationship, Mapped, mapped_column
from app.database import Base
from datetime import datetime

commercial_league_tours = Table(
    "commercial_league_tours",
    Base.metadata,
    Column("commercial_league_id", Integer, ForeignKey("commercial_leagues.id"), primary_key=True),
    Column("tour_id", Integer, ForeignKey("tours.id"), primary_key=True),
    extend_existing=True,
)

commercial_league_squads = Table(
    "commercial_league_squads",
    Base.metadata,
    Column("commercial_league_id", Integer, ForeignKey("commercial_leagues.id"), primary_key=True),
    Column("squad_id", Integer, ForeignKey("squads.id"), primary_key=True),
    extend_existing=True,
)

class CommercialLeague(Base):
    __tablename__ = "commercial_leagues"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    league_id: Mapped[int] = mapped_column(ForeignKey("leagues.id"))
    prize: Mapped[str] = mapped_column(nullable=True)
    logo: Mapped[str] = mapped_column(nullable=True)
    winner_id: Mapped[int] = mapped_column(ForeignKey("squads.id"), nullable=True)

    registration_start: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    registration_end: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    league: Mapped["League"] = relationship(back_populates="commercial_leagues")
    winner: Mapped["Squad"] = relationship(foreign_keys=[winner_id])
    tours: Mapped[list["Tour"]] = relationship(secondary=commercial_league_tours, back_populates="commercial_leagues")
    squads: Mapped[list["Squad"]] = relationship(secondary=commercial_league_squads, back_populates="commercial_leagues")