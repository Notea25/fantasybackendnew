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

    # competition: Mapped["Competition"] = relationship(back_populates="clubs")
    # players: Mapped[list["Player"]] = relationship(back_populates="club")
    #
    # first_club_matches: Mapped[list["Match"]] = relationship(foreign_keys="Match.first_club_id", back_populates="first_club")
    # second_club_matches: Mapped[list["Match"]] = relationship(foreign_keys="Match.second_club_id", back_populates="second_club")
    # winner_matches: Mapped[list["Match"]] = relationship(foreign_keys="Match.winner_id", back_populates="winner")

    def __repr__(self):
        return self.name
