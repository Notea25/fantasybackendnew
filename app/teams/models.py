from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

class Team(Base):
    __tablename__ = "teams"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    logo: Mapped[str] = mapped_column(nullable=True)
    league_id: Mapped[int] = mapped_column(ForeignKey("leagues.id"), nullable=False)

    league: Mapped["League"] = relationship(back_populates="teams")
    players: Mapped[list["Player"]] = relationship(back_populates="team", cascade="all, delete-orphan")
    home_matches: Mapped[list["Match"]] = relationship(foreign_keys="Match.home_team_id", back_populates="home_team", cascade="all, delete-orphan")
    away_matches: Mapped[list["Match"]] = relationship(foreign_keys="Match.away_team_id", back_populates="away_team", cascade="all, delete-orphan")
    squads: Mapped[list["Squad"]] = relationship(back_populates="fav_team")

    def __repr__(self):
        return self.name