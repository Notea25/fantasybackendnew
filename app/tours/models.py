from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, Table, Column, Integer
from app.database import Base
from sqlalchemy import UniqueConstraint
from app.custom_leagues.models import custom_league_tours

tour_matches_association = Table(
    "tour_matches_association",
    Base.metadata,
    Column("tour_id", ForeignKey("tours.id"), primary_key=True),
    Column("match_id", ForeignKey("matches.id"), primary_key=True),
    extend_existing=True,
)

class Tour(Base):
    __tablename__ = "tours"
    id: Mapped[int] = mapped_column(primary_key=True)
    number: Mapped[int] = mapped_column(Integer)
    league_id: Mapped[int] = mapped_column(ForeignKey("leagues.id"))

    __table_args__ = (
        UniqueConstraint("league_id", "number", name="unique_tour_number_per_league"),
    )

    league: Mapped["League"] = relationship(back_populates="tours")
    custom_leagues: Mapped[list["CustomLeague"]] = relationship(secondary=custom_league_tours, back_populates="tours")
    matches: Mapped[list["Match"]] = relationship(
        secondary=tour_matches_association,
        back_populates="tours"
    )
    boosts: Mapped[list["Boost"]] = relationship(back_populates="tour")
    squads: Mapped[list["SquadTour"]] = relationship(back_populates="tour")

    def __repr__(self):
        return f"Tour {self.number}"
