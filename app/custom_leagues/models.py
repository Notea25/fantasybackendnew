from sqlalchemy import Column, Integer, String, ForeignKey, Enum, Boolean, Table
from sqlalchemy.orm import relationship
from app.database import Base
from enum import Enum as PyEnum

class CustomLeagueType(PyEnum):
    COMMERCIAL = "Commercial"
    USER = "User"
    CLUB = "Club"

class CustomLeague(Base):
    __tablename__ = "custom_leagues"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    description = Column(String, nullable=True)
    league_id = Column(Integer, ForeignKey("leagues.id"))
    type = Column(Enum(CustomLeagueType))
    is_public = Column(Boolean, default=False)
    invitation_only = Column(Boolean, default=False)

    league = relationship("League", back_populates="custom_leagues")
    tours = relationship("Tour", secondary="custom_league_tours", back_populates="custom_leagues")
    squads = relationship("Squad", secondary="custom_league_squads", back_populates="custom_leagues")

    def __repr__(self):
        return f"{self.name} ({self.type.value})"

# Ассоциативные таблицы
custom_league_tours = Table(
    "custom_league_tours",
    Base.metadata,
    Column("custom_league_id", Integer, ForeignKey("custom_leagues.id"), primary_key=True),
    Column("tour_id", Integer, ForeignKey("tours.id"), primary_key=True),
)

custom_league_squads = Table(
    "custom_league_squads",
    Base.metadata,
    Column("custom_league_id", Integer, ForeignKey("custom_leagues.id"), primary_key=True),
    Column("squad_id", Integer, ForeignKey("squads.id"), primary_key=True),
)
