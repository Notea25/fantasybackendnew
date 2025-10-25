from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Team(Base):
    __tablename__ = "teams"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    league_id: Mapped[int] = mapped_column(
        ForeignKey("leagues.id"), nullable=False
    )

    home_matches: Mapped[list["Match"]] = relationship(
        "Match", foreign_keys="Match.home_team_id", back_populates="home_team"
    )
    away_matches: Mapped[list["Match"]] = relationship(
        "Match", foreign_keys="Match.away_team_id", back_populates="away_team"
    )

    def __repr__(self):
        return self.name
