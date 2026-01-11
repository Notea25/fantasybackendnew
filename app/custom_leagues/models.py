from sqlalchemy import Column, Integer, String, ForeignKey, Enum, Boolean, DateTime, Table
from sqlalchemy.orm import relationship, Mapped, mapped_column
from app.database import Base
from datetime import datetime

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


class CustomLeague(Base):
    __tablename__ = "custom_leagues"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    description: Mapped[str] = mapped_column(nullable=True)
    league_id: Mapped[int] = mapped_column(ForeignKey("leagues.id"))
    type: Mapped[str] = mapped_column(default='Users')
    is_public: Mapped[bool] = mapped_column(default=False)
    invitation_only: Mapped[bool] = mapped_column(default=False)
    creator_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=True)
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), nullable=True)  # Только для клубных лиг

    registration_start: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    registration_end: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    league: Mapped["League"] = relationship(back_populates="custom_leagues")
    creator: Mapped["User"] = relationship(back_populates="custom_leagues")
    team: Mapped["Team"] = relationship(back_populates="custom_leagues", foreign_keys=[team_id])  # Связь с командой
    tours: Mapped[list["Tour"]] = relationship(secondary=custom_league_tours, back_populates="custom_leagues")
    squads: Mapped[list["Squad"]] = relationship(secondary=custom_league_squads, back_populates="custom_leagues")

    def __repr__(self):
        return f"{self.name} ({self.type})"
